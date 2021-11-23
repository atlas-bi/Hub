
# Ubuntu Build


```sh
apt-get update
apt-get install dh-make devscripts

rename atlas-hub-<version>
cd atlas-hub-<version>

debuild -us -uc

copy files to ppa repo
```

## To run in local docker
```sh
docker run --rm -it -v $(PWD):/atlas ubuntu:latest /bin/bash

apt-get update; \
apt-get install dh-make devscripts -y; \
cd /atlas; \
VERSION=0.0.1-rc.1; \
apt-get remove atlas-hub -y 2>/dev/null; \
rm -r "atlas-hub-$VERSION" 2>/dev/null; \
cp -r "atlas-hub-<version>" "atlas-hub-$VERSION" \
&& cd "atlas-hub-$VERSION" \
&& find . -type f -name "*" -exec sed -i'' -e "s/<version>/$VERSION/g" {} + \
&& debuild --no-tgz-check -us -uc \
&& cd .. \
&& apt-get install ./atlas-hub_*.deb -y


```

## To install a build

```sh
curl -s --compressed "https://atlas-bi.github.io/ppa/deb/KEY.gpg" | sudo apt-key add -
sudo curl -s --compressed -o /etc/apt/sources.list.d/atlas.list "https://atlas-bi.github.io/ppa/deb/atlas.list"
sudo apt update
sudo apt install atlas-hub
