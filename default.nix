# Build Python package.
# Can be installed in the current user profile with:
# nix-env -if .
{ sources ? null }:
let
  deps = import ./nix/deps.nix { inherit sources; };
  inherit (deps) buildPythonPackage lib pkgs installLibs testLibs;
  version = import ./nix/version.nix;

in buildPythonPackage rec {
  pname = "ekklesia-common";
  inherit version;

  src = pkgs.nix-gitignore.gitignoreSource
          [ "cookiecutter" ]
          ./.;

  doCheck = false;
  catchConflicts = false;

  buildInputs = testLibs;
  propagatedBuildInputs = installLibs;

  passthru = {
    inherit deps version;
    inherit (deps) python;
  };
}
