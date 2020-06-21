{ sources ? null }:
with builtins;

let
  sources_ = if (sources == null) then import ./sources.nix else sources;
  pkgs = import sources_.nixpkgs { };
  niv = (import sources_.niv { }).niv;
  cookiecutter = (import ./cookiecutter.nix { inherit pkgs; }).packages.cookiecutter;
  eliotPkgs = (import ./eliot.nix { inherit pkgs; }).packages;
  pdbpp = (import ./pdbpp.nix { inherit pkgs; }).packages.pdbpp;
  inherit ((import "${sources_.poetry2nix}/overlay.nix") pkgs pkgs) poetry2nix poetry;
  python = pkgs.python38;
  overrides = poetry2nix.overrides.withDefaults (
    self: super: {
      munch = super.munch.overridePythonAttrs (
        old: {
          propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.pbr self.setuptools ];
        }
      );
    });

in rec {
  inherit pkgs python;
  inherit (pkgs) lib glibcLocales;

  mkPoetryApplication = { ... }@args:
    poetry2nix.mkPoetryApplication args // {
      inherit overrides;
    };

  inherit (poetry2nix.mkPoetryPackages {
    projectDir = ../.;
    inherit python;
    inherit overrides;
  }) poetryPackages pyProject;

  # Can be imported in Python code or run directly as debug tools
  debugLibsAndTools = [
    python.pkgs.ipython
    pdbpp
  ];

  devLibs = [
    cookiecutter
  ];

  pythonEnv = python.buildEnv.override {
    extraLibs =
      poetryPackages ++
      debugLibsAndTools ++
      devLibs;
    ignoreCollisions = true;
  };

  # Code style and security tools
  linters = with python.pkgs; [
    bandit
    mypy
    pylama
    pylint
    autopep8
    yapf
  ];

  # Various tools for log files, deps management, running scripts and so on
  shellTools = [
    eliotPkgs.eliot-tree
    niv
    pkgs.entr
    pkgs.jq
    pkgs.zsh
    python.pkgs.poetry
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
