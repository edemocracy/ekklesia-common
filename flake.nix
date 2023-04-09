{
  description = "ekklesia-common";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";
    devenv.url = "github:cachix/devenv";
    poetry2nix = {
      url = "github:dpausp/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];
      systems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];

      perSystem = { config, self', inputs', pkgs, system, ... }: let
        deps = import ./nix/deps.nix {
          poetry2nix = inputs'.poetry2nix.legacyPackages;
          poetry = inputs'.poetry2nix.packages.poetry;
          inherit pkgs;
        };

        python_dev_env = pkgs.buildEnv {
          name = "ekklesia-common-dev-env";
          ignoreCollisions = true;
          paths = with deps;
            [ pythonEnv ] ++
            linters;
        };
        # It creates a directory 'pyenv' that is similar to a Python virtualenv.
        # Provides linters and a Python interpreter with runtime dependencies and test tools.
        # Run this file with ./python_dev_env.nix.
        # The 'pyenv' should be picked up py IDE as a possible project interpreter (restart may be required).
        # Used for IDE integration (tested with VSCode, Pycharm).
        buildDevEnvCmd = "nix build .#python_dev_env -o pyenv";
      in
      {
        # Per-system attributes can be defined here. The self' and inputs'
        # module parameters provide easy access to attributes of the same
        # system.
        packages = {
          inherit python_dev_env;
          default = python_dev_env;
        };

        devenv.shells.default =
          {
            name = "ekklesia-common";
            # https://devenv.sh/basics/
            env = {
              PYTHONPATH= "./src";
            };

            # https://devenv.sh/packages/
            packages = deps.shellInputs;

            scripts.build_python_dev_env.exec = buildDevEnvCmd;

            enterShell = ''
              ${buildDevEnvCmd} &
            '';
          };

      };
      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
