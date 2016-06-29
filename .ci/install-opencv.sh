set -x
set -e

name="OpenCV"
folder_name="opencv-2.4.13"
link="https://github.com/Itseez/opencv/archive/2.4.13.zip"

if python -c "import cv2" ; then
  opencv_ver = $(python -c "import cv2; print(cv2.__version__.split('.',1)[0])")
  if [ $opencv_ver -eq 3 ] ; then
    echo $name already installed
    exit 0
  fi
  echo $name found, but it is not version 3.x.
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
  unzip -qq ${name}.zip
  rm ${name}.zip
  cd ${folder_name}
else
  cd ${folder_name}
  rm -rf build
fi

mkdir -p build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=$1 -D BUILD_NEW_PYTHON_SUPPORT=ON ..
make --silent
make install
cd ..

if ! python -c "import cv2" ; then
  echo Installed $name successfully, but the python bindings are still not being found.
  echo Check dependencies and the make log to understand why.
  exit 1
fi

cd ..