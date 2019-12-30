builtins.replaceStrings
  [ "\n" ]
  [ "" ]
  (builtins.readFile
    ../src/ekklesia_common/VERSION)
