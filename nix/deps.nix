{ sources ? null }:
with builtins;

let
  sources_ = if (sources == null) then import ./sources.nix else sources;
  pkgs = import sources_.nixpkgs { };
  poetry2nix = pkgs.callPackage sources_.poetry2nix {};
  python = pkgs.python310;
  inherit (pkgs) lib;


  overrides = poetry2nix.overrides.withDefaults (
    self: super: {
      munch = super.munch.overridePythonAttrs (
        old: {
          propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.pbr ];
        }
      );
      pypugjs = super.pypugjs.overridePythonAttrs (
        old: {
          doCheck = false;
          format = "setuptools";
          propagatedBuildInputs = old.propagatedBuildInputs ++ [
            self.poetry
            self.coverage
          ];
        }
      );
    });

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

  poetryWrapper = pkgs.writeScriptBin "poetry" ''
    export PYTHONPATH=
    unset SOURCE_DATE_EPOCH
    ${poetryPackagesByName.poetry}/bin/poetry "$@"
  '';

in rec {
  inherit pkgs python;
  inherit (pkgs) lib glibcLocales;

  # Can be imported in Python code or run directly as debug tools
  debugLibsAndTools = [
    python.pkgs.ipython
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
    black
    isortWrapper
    mypy
    pylama
    pylint
  ];

  # Various tools for log files, deps management, running scripts and so on
  shellTools = [
    poetryPackagesByName.eliot-tree
    pkgs.niv
    pkgs.entr
    pkgs.jq
    pkgs.zsh
    poetryWrapper
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
