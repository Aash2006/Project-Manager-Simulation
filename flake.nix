{
  description = "Django Project Nix Flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" "x86_64-darwin" "aarch64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        # This environment bundles Python with all your specified requirements
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Core Django framework and dependencies
          django
          asgiref
          sqlparse
          django-extensions 
          django-widget-tweaks
          django-polymorphic

          # Testing tools
          coverage       
          faker
          pytest
          pytest-django
          pytest-cov
          pytest-html
          selenium
          splinter
          webdriver-manager

          # Deployment
          gunicorn
          whitenoise
          
        ]);

        # helper to ensure the scripts use the correct python environment
        envPath = ''export PATH="${pythonEnv}/bin:${pkgs.geckodriver}/bin:${pkgs.chromedriver}/bin:$PATH"'';

        initScript = pkgs.writeShellScriptBin "init-proj" ''
          ${envPath}
          echo "Migrating database..."
          python manage.py migrate
          echo "Seeding database..."
          python manage.py seed
        '';

        runScript = pkgs.writeShellScriptBin "run-proj" ''
          ${envPath}
          export DJANGO_DEBUG="True"
          python manage.py runserver
        '';

        testsScript = pkgs.writeShellScriptBin "tests-proj" ''
          ${envPath}
          pytest
        '';

        seedScript = pkgs.writeShellScriptBin "seed-proj" ''
          ${envPath}
          python manage.py seed
        '';

        unseedScript = pkgs.writeShellScriptBin "unseed-proj" ''
          ${envPath}
          python manage.py flush --noinput
        '';

      in {
        apps = {
          init = { type = "app"; program = "${initScript}/bin/init-proj"; };
          run = { type = "app"; program = "${runScript}/bin/run-proj"; };
          tests = { type = "app"; program = "${testsScript}/bin/tests-proj"; };
          seed = { type = "app"; program = "${seedScript}/bin/seed-proj"; };
          unseed = { type = "app"; program = "${unseedScript}/bin/unseed-proj"; };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ 
            pythonEnv 
            pkgs.geckodriver
            pkgs.chromedriver
            ];
          shellHook = ''
            echo "Django development environment loaded."
            export DJANGO_SETTINGS_MODULE=project.settings 
          '';
        };
      }
    );
}