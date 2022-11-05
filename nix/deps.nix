{ sources ? null }:
with builtins;

let
  sources_ = if (sources == null) then import ./sources.nix else sources;

  poetry2nixSrc = ../../poetry2nix;
  #poetry2nixSrc = "${sources_.poetry2nix}";
  # Taken from overlay.nix from poetry2nix, adapted for python310
  pkgs = import sources_.nixpkgs {
    overlays = [(final: prev: {
      poetry2nix = import poetry2nixSrc { pkgs = final; poetry = final.poetry; };
      poetry = prev.callPackage "${poetry2nixSrc}/pkgs/poetry" { python = final.python310; };
    })];
  };
  python = pkgs.python310;
  inherit (pkgs) poetry poetry2nix lib;

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
            self.poetry
          ];
        }
      );
    } //
    (addPythonBuildDeps
      [ self.setuptools_scm ]
      [ "more-babel-i18n" "pdbpp" ])

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

in rec {
  inherit pkgs python poetryPackagesByName;
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
    #isortWrapper
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
