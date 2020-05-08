{ pkgs, python }:

with pkgs.python38Packages;

let
  addBuiltInputs = packageName: inputs:
    {
      "${packageName}" = python.overrideDerivation super."${packageName}" (old: {
        buildInputs = old.buildInputs ++ inputs;
      });
    };
in

self: super: {
  inherit (pkgs) zsh;

  "setuptools-scm" = setuptools_scm;

  "py" = python.overrideDerivation super."py" (old: {
    buildInputs = old.buildInputs ++ [ setuptools_scm ];
  });

  "pytest-mock" = python.overrideDerivation super."pytest-mock" (old: {
    buildInputs = old.buildInputs ++ [ setuptools_scm ];
  });

  "faker" = python.overrideDerivation super."faker" (old: {
    buildInputs = old.buildInputs ++ [ pytestrunner ];
  });
}
