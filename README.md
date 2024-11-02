![](.github/banner.png)

JWizard is an open-source Discord music bot handling audio content from various multimedia sources with innovative web
player. This repository contains scripts that automate operations in the CI/CD pipelines of other JWizard projects, as
well as standalone scripts used in various JWizard projects.

## Table of content

* [Project modules](#project-modules)
* [Clone and install](#clone-and-install)
* [Project arguments](#project-arguments)
* [License](#license)

## Project modules

| Name             | Description                                                    |
|------------------|----------------------------------------------------------------|
| packages_grabber | Parsing and persisting packages used in all JWizard projects.  |
| db_migrator      | Database migrator, modifying structure and data via SQL files. |

## Clone and install

1. Make sure you have at least Python 3 (tested on 3.14) at your machine.
2. Clone this repository via:

```bash
$ git clone https://github.com/jwizard-bot/jwizard-tools
```

3. Prepare Python virtual environment via:

```bash
$ python -m venv .venv
```

4. Activate environment via:

* for UNIX environments:

```bash
$ source .venv/bin/activate
```

* for Windows environments:

```cmd
.\.venv\bin\Activate.ps1
```

> NOTE: If you have an execution policy error, try execute `Set-ExecutionPolicy RemoteSigned` in PowerShell.

5. Install project-related dependencies via:

```bash
$ (venv) pip install -r requirements.txt
```

6. Run script via:

```bash
$ (venv) python src/<project name>.py <arguments>
```

Where `<project name>` is name of the project (defined in *name* column in **Project modules** table).

> NOTE: If `python` command not working in UNIX-like shells (ex. ZSH), try run via `python3` command.

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

Where `<project name>` is name of the project (defined in *name* column in **Project modules** table).

## Project arguments

* For all projects:

<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>--vault-address</td>
      <td>No, default: http://localhost:8761</td>
      <td>Vault KV storage address.</td>
    </tr>
    <tr>
      <td>--vault-token</td>
      <td>Yes, if not authenticated as userpass.</td>
      <td>Vault KV storage access token.</td>
    </tr>
    <tr>
      <td rowspan="2">--vault-username, <br> --vault-password</td>
      <td>Yes, if not authenticated as token.</td>
      <td>Vault KV storage username and password.</td>
    </tr>
  </tbody>
</table>

* For `packages_grabber` project:

<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>--repo</td>
      <td>Yes</td>
      <td>Github repository name and organization: owner/name.</td>
    </tr>
  </tbody>
</table>

* For `db_migrator` project:

<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>

## License

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.
