# CryptoStats

My goal is to develop a container application to analyze crypocurrencies.

## Architecture

![Architecture](architecture/architecture.svg)

## Start the app

Copy the content of `prod.yml` to your PC in a file named `docker-compose.yml` and start the app with:

```bash
docker login
docker-compose up -d
```

NB: to download the historical data it takes many hours.

## Monitor the app

```bash
docker-compose logs -f
docker ps
docker stats
```

## Contribute

If you want to contribute to this project check the [development guide](dev/README.md).

## Troubleshooting

Please check [this document](dev/troubleshooting.md).
