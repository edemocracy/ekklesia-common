{ pkgs, poetry2nix }:

with builtins;

let
  python = pkgs.python311;
  poetry = (pkgs.poetry.override { python3 = python; });
  inherit (pkgs) lib;

  overrides = poetry2nix.overrides.withDefaults (
    self: super:
    let
      pythonBuildDepNameValuePair = deps: pname: {
        name = pname;
        value = super.${pname}.overridePythonAttrs (old: {
          buildInputs = old.buildInputs ++ deps;
        });
      };

      addPythonBuildDeps = deps: pnames:
        lib.listToAttrs
          (map
            (pythonBuildDepNameValuePair deps)
            pnames);
    in
    {
      munch = super.munch.overridePythonAttrs (
        old: {
          buildInputs = old.buildInputs ++ [ self.pbr ];
        }
      );
      pypugjs = super.pypugjs.overridePythonAttrs (
        old: {
          doCheck = false;
          format = "setuptools";
          buildInputs = old.buildInputs ++ [
            self.coverage
            self.poetry-core
          ];
        }
      );
    } //
    (addPythonBuildDeps [ self.poetry-core ] [
      "more-browser-session"
      "more-babel-i18n"
    ]) //
    (addPythonBuildDeps [ self.flit-core ] [
      "cloudpickle"
      "colored"
    ]) //
    (addPythonBuildDeps [ self.setuptools-scm self.setuptools ] [
      "pdbpp"
    ]) //
    (addPythonBuildDeps [ self.setuptools ] [
      "case-conversion"
      "base32-crockford"
      "babel"
      "fancycompleter"
      "better-exceptions"
      "py-gfm"
      "pyrepl"
      "pytest-pspec"
      "wmctrl"]) //
    (addPythonBuildDeps
    [ self.hatchling ] [ 
      "beautifulsoup4"
      "urllib3"
    ]) //
    (addPythonBuildDeps
      [ self.greenlet ] [
        "sqlalchemy"
        "sqlalchemy-utils"
        "zope-sqlalchemy"
     ])
    );

  inherit (poetry2nix.mkPoetryPackages {
    projectDir = ../.;
    inherit python;
    inherit overrides;
  }) poetryPackages;

  poetryPackagesByName =
    lib.listToAttrs
      (map
        (p: { name = p.pname or "none"; value = p; })
        poetryPackages);


  aiohttp383 = python.pkgs.aiohttp.overrideAttrs(_: rec {
	  pname = "aiohttp";
    version = "3.8.3";
    name = "aiohttp-3.8.3";

    src = python.pkgs.fetchPypi {
      inherit pname version;
      hash = "sha256-OCj7QbcgMXa4L+XWmeDYRUNfI3R1CkS0gOprkw9r4mk=";
    };
  });

in rec {
  inherit pkgs python poetryPackagesByName;
  inherit (pkgs) lib glibcLocales;

  # Can be imported in Python code or run directly as debug tools
  debugLibsAndTools = [
    #python.pkgs.ipython
  ];

  pythonEnv = python.buildEnv.override {
    extraLibs =
      poetryPackages ++
      debugLibsAndTools;
    ignoreCollisions = true;
  };

  # Code style and security tools
  linters = with python.pkgs; let
    isortWrapper = with python.pkgs; pkgs.writeScriptBin "isort" ''
      ${isort}/bin/isort --virtual-env=${pythonEnv} --profile=black "$@"
    '';
  in [
    bandit
    #(black.override { aiohttp = aiohttp383; aiohttp-cors = null; })
    #isortWrapper
    mypy
    #pylama
    #pylint
  ];

  # Various tools for log files, deps management, running scripts and so on
  shellTools = [
    poetryPackagesByName.eliot-tree
    pkgs.entr
    pkgs.jq
    pkgs.zsh
    poetry
  ];

  # Needed for a development nix shell
  shellInputs =
    linters ++
    shellTools ++
    debugLibsAndTools ++ [
      pythonEnv
    ];

  shellPath = lib.makeBinPath shellInputs;
}
