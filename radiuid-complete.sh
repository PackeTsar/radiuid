#!/bin/bash

#####  RadiUID Server BASH Complete Script  #####
#####        Written by John W Kerns        #####
#####       http://blog.packetsar.com       #####
#####  https://github.com/PackeTsar/radiuid #####

_radiuid_complete()
{
  local cur prev
  COMPREPLY=()
  cur=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}
  prev2=${COMP_WORDS[COMP_CWORD-2]}
  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=( $(compgen -W "run install show set push tail clear edit service request version" -- $cur) )
  elif [ $COMP_CWORD -eq 2 ]; then
    case "$prev" in
      show)
        COMPREPLY=( $(compgen -W "log acct-logs run config clients status mappings" -- $cur) )
        ;;
      "set")
        COMPREPLY=( $(compgen -W "tlsversion radiusstopaction looptime logfile maxloglines radiuslogpath userdomain timeout target client munge" -- $cur) )
        ;;
      push)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        ;;
      "tail")
        COMPREPLY=( $(compgen -W "log" -- $cur) )
        ;;
      "clear")
        COMPREPLY=( $(compgen -W "log acct-logs target mappings client munge" -- $cur) )
        ;;
      edit)
        COMPREPLY=( $(compgen -W "config clients" -- $cur) )
        ;;
      "service")
        COMPREPLY=( $(compgen -W "radiuid freeradius all" -- $cur) )
        ;;
      "request")
        COMPREPLY=( $(compgen -W "xml-update munge-test auto-complete reinstall freeradius-install" -- $cur) )
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 3 ]; then
    case "$prev" in
      run)
        COMPREPLY=( $(compgen -W "xml set <cr>" -- $cur) )
        ;;
      config)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "xml set <cr>" -- $cur) )
        fi
        ;;
      reinstall)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "replace-config keep-config" -- $cur) )
        fi
        ;;
      freeradius-install)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "<cr> no-confirm" -- $cur) )
        fi
        ;;
      munge-test)
        if [ "$prev2" == "request" ]; then
          COMPREPLY=( $(compgen -W "- <string-to-parse>" -- $cur) )
        fi
        ;;
      client)
        local clients=$(for client in `radiuid clients`; do echo $client ; done)
        if [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${clients} all" -- ${cur}) )
        elif [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "- <ip-block>" -- ${cur}) )
        fi
        ;;
      clients)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "file table <cr>" -- ${cur}) )
        fi
        ;;
      radiuslogpath)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<directory-path> -" -- $cur) )
        fi
        ;;
      logfile)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<file-path> -" -- $cur) )
        fi
        ;;
      maxloglines)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-lines> -" -- $cur) )
        fi
        ;;
      looptime)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-seconds> -" -- $cur) )
        fi
        ;;
      tlsversion)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "1.0 1.1 1.2" -- $cur) )
        fi
        ;;
      radiusstopaction)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "clear ignore push" -- $cur) )
        fi
        ;;
      userdomain)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<domain-name> none" -- $cur) )
        fi
        ;;
      timeout)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "<number-of-minutes> -" -- $cur) )
        fi
        ;;
      freeradius|radiuid)
        if [ "$prev2" == "service" ]; then
          COMPREPLY=( $(compgen -W "start stop restart" -- $cur) )
        fi
        ;;
      log)
        if [ "$prev2" == "tail" ]; then
          COMPREPLY=( $(compgen -W "- <number-of-lines> <cr>" -- $cur) )
        fi
        ;;
      all)
        if [ "$prev2" == "service" ]; then
          COMPREPLY=( $(compgen -W "start stop restart" -- $cur) )
        elif [ "$prev2" == "push" ]; then
          COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
        fi
        ;;
      mappings)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        if [ "$prev2" == "show" ]; then
          COMPREPLY=( $(compgen -W "${targets} all consistency" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        fi
        ;;
      target)
        local targets=$(for target in `radiuid targets`; do echo $target ; done)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W "${targets} - <NEW-HOSTNAME>:<VSYS-ID>" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          COMPREPLY=( $(compgen -W "${targets} all" -- ${cur}) )
        fi
        ;;
      munge)
        if [ "$prev2" == "set" ]; then
          COMPREPLY=( $(compgen -W " - <rule>.<step>" -- ${cur}) )
        elif [ "$prev2" == "clear" ]; then
          local rules=$(for rule in `radiuid munge-rules`; do echo $rule ; done)
          COMPREPLY=( $(compgen -W "${rules} all" -- ${cur}) )
        fi
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 4 ]; then
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    if [ "$prev2" == "mappings" ]; then
      if [ "$prev3" == "clear" ]; then
        COMPREPLY=( $(compgen -W "all <uid-ip>" -- $cur) )
      fi
    fi
    if [ "$prev2" == "all" ]; then
      if [ "$prev3" == "push" ]; then
        COMPREPLY=( $(compgen -W "<ip-address> -" -- $cur) )
      fi
    fi
    if [ "$prev2" == "client" ]; then
      if [ "$prev3" == "set" ]; then
        COMPREPLY=( $(compgen -W "<shared-secret> -" -- $cur) )
      fi
    fi
    if [ "$prev2" == "munge" ]; then
      if [ "$prev3" == "clear" ]; then
        if [ "$prev" != "all" ]; then
          local steps=$(for step in `radiuid munge-steps $prev`; do echo $step ; done)
          COMPREPLY=( $(compgen -W "${steps} all" -- $cur) )
        fi
      fi
    fi
    if [ "$prev2" == "munge-test" ]; then
      if [ "$prev3" == "request" ]; then
        COMPREPLY=( $(compgen -W "<cr> debug" -- $cur) )
      fi
    fi
    if [ "$prev2" == "munge" ]; then
      if [ "$prev3" == "set" ]; then
        IFS='.' read -a myarray <<< "$prev"
        if [ "${myarray[1]}" == "0" ]; then
          COMPREPLY=( $(compgen -W "match" -- $cur) )
        elif [ "${myarray[1]}" != "0" ]; then
          COMPREPLY=( $(compgen -W "accept assemble discard set-variable" -- $cur) )
        fi
      fi
    fi
    if [ "$prev2" == "reinstall" ]; then
      if [ "$prev3" == "request" ]; then
        COMPREPLY=( $(compgen -W "<cr> no-confirm" -- $cur) )
      fi
    fi
  elif [ $COMP_CWORD -eq 5 ]; then
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    if [ "$prev4" == "push" ]; then
      if [ "$prev3" != "all" ]; then
        COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "set-variable" ]; then
        COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "assemble" ]; then
        COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
      fi
    fi
    if [ "$prev3" == "munge" ]; then
      if [ "$prev" == "match" ]; then
        IFS='.' read -a myarray <<< "$prev2"
        if [ "${myarray[1]}" == "0" ]; then
          COMPREPLY=( $(compgen -W "any <regex-pattern>" -- $cur) )
        fi
      fi
    fi
    if [ "$prev3" == "all" ]; then
      if [ "$prev4" == "push" ]; then
        COMPREPLY=( $(compgen -W "bypass-munge <cr>" -- $cur) )
      fi
    fi
  elif [ $COMP_CWORD -eq 6 ]; then
    prev2=${COMP_WORDS[COMP_CWORD-2]}
    prev3=${COMP_WORDS[COMP_CWORD-3]}
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    prev5=${COMP_WORDS[COMP_CWORD-5]}
    if [ "$prev4" == "mappings" ]; then
      if [ "$prev5" == "clear" ]; then
        COMPREPLY=( $(compgen -W "all <uid-ip>" -- $cur) )
      fi
    elif [ "$prev5" == "push" ]; then
      COMPREPLY=( $(compgen -W "<ip-address> -" -- $cur) )
    fi
    if [ "$prev4" == "target" ]; then
      if [ "$prev5" == "set" ]; then
        COMPREPLY=( $(compgen -W "username password version" -- $cur) )
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "assemble" ]; then
          COMPREPLY=( $(compgen -W "- <variable-name>" -- $cur) )
        fi
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "set-variable" ]; then
          COMPREPLY=( $(compgen -W "from-match from-string" -- $cur) )
        fi
      fi
    fi
    if [ "$prev4" == "munge" ]; then
      if [ "$prev5" == "set" ]; then
        if [ "$prev2" == "match" ]; then
          IFS='.' read -a myarray <<< "$prev3"
          if [ "${myarray[1]}" == "0" ]; then
            if [ "$prev" != "any" ]; then
              COMPREPLY=( $(compgen -W "complete partial" -- $cur) )
            fi
          fi
        fi
      fi
    fi
  elif [ $COMP_CWORD -eq 8 ]; then
    case "$prev2" in
      username)
        COMPREPLY=( $(compgen -W "password version" -- $cur) )
        ;;
      password)
        COMPREPLY=( $(compgen -W "username version" -- $cur) )
        ;;
      version)
        COMPREPLY=( $(compgen -W "username password" -- $cur) )
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 10 ]; then
    prev4=${COMP_WORDS[COMP_CWORD-4]}
    case "$prev4" in
      username)
        if [ "$prev2" == "password" ]; then
            COMPREPLY=( $(compgen -W "version" -- $cur) )
        elif [ "$prev2" == "version" ]; then
            COMPREPLY=( $(compgen -W "password" -- $cur) )
        fi
        ;;
      password)
        if [ "$prev2" == "username" ]; then
            COMPREPLY=( $(compgen -W "version" -- $cur) )
        elif [ "$prev2" == "version" ]; then
            COMPREPLY=( $(compgen -W "username" -- $cur) )
        fi
        ;;
      version)
        if [ "$prev2" == "username" ]; then
            COMPREPLY=( $(compgen -W "password" -- $cur) )
        elif [ "$prev2" == "password" ]; then
            COMPREPLY=( $(compgen -W "username" -- $cur) )
        fi
        ;;
      *)
        ;;
    esac
  elif [ $COMP_CWORD -eq 7 ]; then
    if [ "$prev" == "username" ]; then
      COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
    fi
    if [ "$prev" == "password" ]; then
      COMPREPLY=( $(compgen -W "<password> -" -- $cur) )
    fi
    if [ "$prev" == "version" ]; then
      COMPREPLY=( $(compgen -W "<pan-os-version> -" -- $cur) )
    fi
    if [ "$prev" == "from-match" ]; then
      COMPREPLY=( $(compgen -W "<regex-pattern> any" -- $cur) )
    fi
    if [ "$prev" == "from-string" ]; then
      COMPREPLY=( $(compgen -W "<string> -" -- $cur) )
    fi
    if [ "$prev5" == "push" ]; then
      COMPREPLY=( $(compgen -W "bypass-munge <cr>" -- $cur) )
    fi
  elif [ $COMP_CWORD -eq 9 ] || [ $COMP_CWORD -eq 11 ]; then
    case "$prev" in
      username)
        COMPREPLY=( $(compgen -W "<username> -" -- $cur) )
        ;;
      password)
        COMPREPLY=( $(compgen -W "<password> -" -- $cur) )
        ;;
      version)
        COMPREPLY=( $(compgen -W "<pan-os-version> -" -- $cur) )
        ;;
      from-match)
        COMPREPLY=( $(compgen -W "<regex-pattern> any" -- $cur) )
        ;;
      from-string)
        COMPREPLY=( $(compgen -W "<string> -" -- $cur) )
        ;;
      *)
        ;;
    esac
  fi
  return 0
} &&
complete -F _radiuid_complete radiuid &&
bind 'set show-all-if-ambiguous on'