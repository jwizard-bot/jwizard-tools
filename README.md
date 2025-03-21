![](.github/banner.png)

[[About project](https://jwizard.pl/about)]

JWizard is an open-source Discord music bot handling audio content from various multimedia sources
with innovative web player. This repository contains scripts that automate operations in the CI/CD
pipelines of other JWizard projects, as well as standalone scripts used in various JWizard projects.

## Table of content

* [Project modules](#project-modules)
* [Clone and install](#clone-and-install)
* [Create migration](#create-migration)
* [Project arguments](#project-arguments)
* [License](#license)

## Project modules

| Name             | Description                                                                                |
|------------------|--------------------------------------------------------------------------------------------|
| packages_grabber | Parsing and persisting packages used in all JWizard projects.                              |
| db_migrator      | Database migrator framework, modifying structure and data via YAML files with SQL content. |
| cache_version    | Update deployment cache (project version and time) in DB.                                  |

## Clone and install

1. Make sure you have at least Python 3 (tested on 3.14) at your machine.
2. Clone this repository via:

```bash
$ git clone https://github.com/jwizard-bot/jwizard-tools
```

3. Create `.env` file based `example.env` with following properties:

```properties
ENV_VAULT_TOKEN=<token>
```

4. Prepare Python virtual environment via:

```bash
$ python -m venv .venv
```

5. Activate environment via:

* for UNIX environments:

```bash
$ source .venv/bin/activate
```

* for Windows environments:

```cmd
.\.venv\bin\Activate.ps1
```

> [!TIP]
> If you have an execution policy error, try to execute
> `Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser` in PowerShell.

> [!TIP]
> If you don't have `bin` directory, change path to `.venv/Scripts/activate` and
> `.\.venv\Scripts\Activate.ps1` for UNIX and Windows environments respectively.

6. Install project-related dependencies via:

```bash
$ (venv) pip install -r requirements.txt
```

7. Run script via:

```bash
$ (venv) python src/<project name>.py <arguments>
```

Where `<project name>` is name of the project (defined in *name* column in **Project modules**
table).

> [!TIP]
> If `python` command not working in UNIX-like shells (ex. ZSH), try run via `python3` command.

### Alternative, only for UNIX environments:

Make sure you have required permissions:

```bash
$ sudo chmod +x exec/prepare
$ sudo chmod +x exec/run
```

1. Prepare virtual environment and install dependencies via:

```bash
$ exec/prepare
```

2. Run via:

```bash
$ exec/run <project name> <additional arguments>
```

Where `<project name>` is name of the project (defined in *name* column in **Project modules**
table).

## Create migration

To create migration template file (in UNIX environments), type:

```bash
$ sudo chmod +x exec/create-migration
$ exec/create-migration <migration name> <pipeline> <author>
```

where:

* `<migration name>` is the self descriptive name of the migration file,
* `<pipeline>` is one of the migration base directory (see `--pipeline` argument for `db_migrator`
  project),
* `<author` is migration author persisted in DB. By default, gets author from git property
  `user.name`. Not required.

This script will automatically created new migration template with current date, incremented
migration number and base migration script copied from `migrations/template.yml` file.

## Project arguments

* For `packages_grabber` project:

```js
--repo(required)     // Github repository name and organization: owner/name.
```

* For `db_migrator` project:

```js
--pipeline(required) // Determine from which directory migrator execute migrations (take: 'infra'
                     // and 'self'). Used for separate migration executions for JWizard Tools and
                     // JWizard Infra (Core and API).
```

* For `cache_version` project:

```js
--repo(required)     // Github repository name and organization: owner/name.
```

* For `project_analyzer` project:

```js
--repo(required)     // Github repository name and organization: owner/name.
```

## License

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.
