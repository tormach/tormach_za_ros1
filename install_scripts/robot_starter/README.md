# Tormach PathPilot Robot Starter
[_metadata_:author]:-  "Jakub Fišer <jakub DOT fiser AT eryaf DOT com>"
[_metadata_:description]:- "Robot Starter package README"
[_metadata_:url-repo]:- "https://bitbucket.org/tormachinc/ros"

Tormach PathPilot Robot Starter package should include all tools and dependencies for starting the PathPilot Robot Launcher.

**Distributing the actual PathPilot Robot Docker image is out of scope for this package!**

## Provides
*   The **launch-pathpilot-launcher** executable script
*   The **starter_splash** splash-screen Python module with an entry point executable
*   The **Tormach** menu in the _Application_ mount-point
*   The **robot-launcher.desktop** file for starting the PathPilot Robot Launcher from the start menu and user's desktop shortcut
*   Set of basic icons

## Additional functionality
*   At first install of the Debian package, _preinst_ script is run which removes the manually installed files from first robot's deployment

## Debian packages
* **pathpilotrobotstarter**

## HOWTO
* Runt the `install_scripts/docker-dev.sh` script with arguments `-E {some_existing_path}` to export the built artifacts from the DIST PathPilot Robot Docker image
* Install the package with `sudo apt install {some_existing_path}/deb/*.deb`

## TODO and missing
*   Use the EULA from main **changelog** file for the Debian **copyright** file, so the information is not duplicated
* Add testing and run it during build (somehow, not sure how now)
