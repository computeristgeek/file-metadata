set -x
set -e

name="python-gi"
folder_name="pygobject-3.16.2"
link="http://ftp.gnome.org/pub/GNOME/sources/pygobject/3.16/pygobject-3.16.2.tar.xz"

if python -c "import gi" ; then
  echo $name already installed
  exit 0
fi

if [ "a${1}a" == "aa" ] ; then
  echo "No location provided to install $name in."
  exit 1
fi

if [ ! -d "$folder_name" ] ; then
  echo Downloading $name ...
  # Using -q in wget makes OSX hang sometimes
  wget $link -O ${name}.tar.xz
  echo Unpacking $name ...
  tar -xJf ${name}.tar.xz
  rm ${name}.tar.xz
  cd ${folder_name}
else
  cd ${folder_name}
  make clean
fi

./configure --prefix=$1
make
make install

cd ..
