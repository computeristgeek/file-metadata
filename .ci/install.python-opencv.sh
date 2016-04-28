set -x
set -e

name="python-opencv"
folder_name="opencv-2.4.12"
link="https://github.com/Itseez/opencv/archive/2.4.12.zip"

if python -c "import cv" ; then
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
  make clean
fi

mkdir -p build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=$1 -D BUILD_NEW_PYTHON_SUPPORT=ON ..
make
make install
cd ..

cd ..
