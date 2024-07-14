# Rehau Nea Smart 2.0 Home Assistant Integration

## Important Notice
- **Development Stage:** This integration is currently in development and is not yet recommended for production use. Please proceed at your own risk. The developer assumes no responsibility for any potential damage caused by using this integration.
- **Not Affiliated:** This integration is not affiliated with Rehau in any manner.

## Overview

The Rehua Nea Smart 2.0 Home Assistant Integration empowers you to control and monitor your Rehua Nea Smart 2.0 climate control device directly through Home Assistant.

## Features

- **Climate Control:** Effortlessly set and monitor temperature along with other climate control parameters.
- **Seamless Integration:** Enjoy a unified smart home experience with seamless integration into Home Assistant.

## Known Limitations

- **Multiple Installations:** The integration currently only tested with a single installation linked to the Rehua account. Multiple installations may not work as expected.
- **Multiple rooms:** The integration is currently only tested with a single room with multiple zones. Multiple rooms may not work as expected.
- **Limited Functionality:** The integration currently only supports basic climate control functionality. Advanced features such as scheduling are not supported.
- **Global Heatmode:** The Nea Smart Controller only supports a global heat mode. This means that the changes made to the heat mode will affect all zones.

## Installation

### Prerequisites
- Ensure that you have already set up a Rehua Nea Smart 2.0 account and successfully linked your device to your account.
- Remember to check "Always use this installation on startup" in your App or the installation will not be found.

### HACS (Home Assistant Community Store)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=rehau-nea-smart-2.0-ha&owner=th3r3alandr3)
1. Add this repository as a custom repository in HACS.
2. Search for the Rehua Nea Smart 2.0 Integration and proceed with the installation.
3. Restart Home Assistant.
4. Navigate to Settings -> Devices and Services -> Integrations and add the Rehua Nea Smart 2.0 Integration.

## Troubleshooting
- Should you encounter any issues with the integration, kindly open an issue on the GitHub repository for prompt assistance.

## Contributing
- Contributions are welcome. Please open an issue on the GitHub repository to discuss any proposed changes before submitting a pull request.
