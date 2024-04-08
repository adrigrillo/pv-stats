# checking for group...uid is $1, gid is $2 and user is $3
if ! getent group | grep -q ":$2:"; then
  addgroup --gid "$2" "$3"
fi
# checking for user...uid is $1, gid is $2 and user is $3
if ! getent passwd | grep -q ":$1:"; then
  adduser --uid "$1" --gid "$2" --disabled-password --gecos "" "$3"
  echo "$3 ALL=(ALL) NOPASSWD:ALL" >>/etc/sudoers
fi
