set -x
set -e

name="python-pyexiv2"
folder_name="pyexiv2-master"
link="https://github.com/escaped/pyexiv2/archive/master.zip"

if python -c "import pyexiv2" ; then
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
  wget $link -O ${name}.zip
  echo Unpacking $name ...
  unzip ${name}.zip
  rm ${name}.zip
  cd ${folder_name}
else
  cd ${folder_name}
fi

pip install .

cd ..
