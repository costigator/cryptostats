# Deployment on production

If you want run this app on a productive system follow this guide.

## Start

```bash
git clone https://github.com/costigator/cryptostats.git
cd cryptostats/prod
docker login
docker-compose up -d
```

NB: to download the historical data it takes many hours.

## Monitor

```bash
docker-compose logs -f
docker ps
docker stats
```

## Update

```bash
cd cryptostats/prod
./update.sh
```

## Automatic Update

Install a crontab job (it will be executed every 2 min):

```bash
crontab -e
*/2 * * * * cd ~/Repos/cryptostats/prod/ && ./update.sh >> ~/cryptostats-update.log 2>&1
```
