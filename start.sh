#!/bin/bash -e

# Configuration file
ENVFILE='.env'

# Mandatory VARS
# You can define custom values here or in $ENVFILE. Otherwise, we'll generate random values for you :)
declare -A vars
vars[SECRET_KEY]=''
vars[ALLOWED_HOSTS]='127.0.0.1 localhost'
vars[DATABASE_PASSWORD]=''

# Default docker-compose file
dcfile='docker-compose.yml'

print_help() {
  NAME="$(basename "$0")"
  cat <<EOF

Usage: $NAME [-h|--help] [-f file] [services]

  [Optional] -h, --help:      Print this help
  [Optional] -f file:         Define docker-compose file to execute.
  [Optional] services:        Define a list of docker-compose services to run.
                              Available services: ${services[*]}
EOF
  exit
}

generate_secret() {
  echo "Creating a new random $varkey"
  rndSecret="$(python3 -c "import secrets; print(secrets.token_urlsafe(37))")"
  addVarToEnvFile "$varkey" "$rndSecret"
}

addVarToEnvFile() {
  var="$1"
  value="$2"
  echo "Adding $var to '$ENVFILE' file:"
  echo -e "    $var=${value}\n"
  echo "$var=${value}" >> $ENVFILE
}

checkVars() {
  for varkey in "${!vars[@]}"; do
    if ! grep -q "^ *$varkey" $ENVFILE ; then
      echo "WARNING: Required variable '$varkey' missing."
      case $varkey in
        "SECRET_KEY" )
          if [ -z "${vars[$varkey]}" ]; then
            generate_secret
          else
            addVarToEnvFile "$varkey" "${vars[$varkey]}"
          fi
          ;;
        "DATABASE_PASSWORD" )
          if [ -z "${vars[$varkey]}" ]; then
            generate_secret
          else
            addVarToEnvFile "$varkey" "${vars[$varkey]}"
          fi
          ;;
        "ALLOWED_HOSTS" )
          addVarToEnvFile "$varkey" "${vars[$varkey]}"
          ;;
        * )
          echo "Variable ${varkey} is mandatory. Please read documentation"
          ;;
      esac
    fi
  done
}

processArgs(){
  while (( "$#" )); do
    if [[ "$1" == "-f" ]] ; then
      if [[ -a "$2" ]] ; then
        dcfile="$2"
        shift 2
        continue
      else
        echo "ERROR: docker-compose file '$2' not found"
        print_help
      fi
    elif ( [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]] ) ; then
        print_help
    elif [[ ! " ${availServs[*]} " =~ " ${1} " ]]; then
      echo "ERROR: Service $1 not available"
      print_help
    else
      selectedServs+=("$1")
      shift
    fi
  done
}

checkVars

selectedServs=()
availServs=( $(docker-compose config --services) )
processArgs $@

if ((${#selectedServs[@]})); then
  docker-compose -f $dcfile up -d ${selectedServs[*]}
else
  # IF no services have been specified, we will build and run all
  docker-compose -f $dcfile up -d
fi


  cat <<EOF

Services status:
$(docker-compose ps)

If this is the first time you build the application, you should create a user executing the following command:

  docker-compose exec app python homodaba/manage.py createsuperuser

You can check de application at http://127.0.0.1:8000/admin/
EOF
