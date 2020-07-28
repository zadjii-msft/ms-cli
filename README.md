# ms-cli
A commandline interface for the Microsoft Graph

Have you ever wanted to be able to send Teams messages directly from your terminal? Or open multiple chat windows side-by-side? Maybe you want to be able to browse your files in OneDrive directly from the commandline?

With the `ms` CLI tool, you can interact with any applications connected to the Microsoft Graph directly from the commandline. This enables users to be able to do things like:

- Chat directly with other users from the commandline
- Open up a channel in Teams, and create new threads or send replies to threads
- Browse their files in OneDrive with familiar commands
- Upload files to OneDrive or download them locally
- View and send emails in Outlook
- and much much more

![teams-side-by-side](blob/master/screenshots/teams-side-by-side.png)

Leveraging the power of the [Windows Terminal](https://github.com/microsoft/terminal), users can have multiple chat threads open in a single window side-by-side, by using [panes](https://docs.microsoft.com/en-us/windows/terminal/panes) in the Terminal.

Checkout more [screenshots](blob/master/screenshots).

## Contributing

After cloning the repo, run `pip install -r requirements.txt`

### Code formatting

This project uses [`black`](https://github.com/psf/black) for code formatting.
To format the code, run `black .`. You might need to add your python scripts
directory to your path. For me, this was done with:

```
set PATH=%PATH%;%localappdata%\Packages\PythonSoftwareFoundation.Python.3.7_qbz5n2kfra8p0\LocalCache\local-packages\Python37\Scripts
```
