
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
# change into the packages directory.
cd packages

# start up a docker.
docker run --rm -it -p 8080:80 -v $(PWD):/atlas ubuntu:latest /bin/bash

# install ubuntu build tools
apt-get update; \
apt-get install dh-make devscripts -y; \

# change to the "package" folder
cd /atlas; \

# set the version
VERSION=0.0.1-rc.4; \

# uninstall old verions
apt-get remove atlas-hub -y 2>/dev/null; \
rm -r "atlas-hub-$VERSION" 2>/dev/null; \

# build new version, and install it
cp -r "atlas-hub-<version>" "atlas-hub-$VERSION" \
&& cd "atlas-hub-$VERSION" \
&& find . -type f -name "*" -exec sed -i'' -e "s/<version>/$VERSION/g" {} + \
&& debuild --no-tgz-check -us -uc \
&& cd .. \
&& apt-get install ./atlas-hub_*.deb -y

# or
&& EXPORT EXTERNAL_URL="$HOSTNAME"; apt-get install ./atlas-hub_*.deb -y

```

## To install a build

```sh
curl -s --compressed "https://atlas-bi.github.io/ppa/deb/KEY.gpg" | sudo apt-key add -
sudo curl -s --compressed -o /etc/apt/sources.list.d/atlas.list "https://atlas-bi.github.io/ppa/deb/atlas.list"
sudo apt update
sudo apt install atlas-hub

# or to specify the external url directory
EXPORT EXTERNAL_URL='https://google.com'; sudo apt install atlas-hub

```

## Where the files should end up

`usr/bin/atlas-hub` > cli application
`usr/lib/atlas-hub`  > install directory for webapp
`etc/atlas-hub` > config directory
`var/log/atlas-hub` > log directory
