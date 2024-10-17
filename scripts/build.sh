# Optional uuid to tag the build
UUID=$(uuidgen | tr A-F a-f)
echo "Building save-it..."

poetry export -f requirements.txt --output requirements.txt --without-hashes
docker build -t manelfideles/save-it .
