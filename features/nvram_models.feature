Feature: Hardware model NVRAM firmware validation

  Each hardware model directory ships PK/KEK/db/dbx EFI variables and a
  custom_VARS.builder.xml. Building it into custom_VARS.fd and booting a
  guest image with it should succeed.

  Scenario Outline: Build and boot NVRAM firmware for a hardware model
    Given the hardware model directory "<model>"
    When I extract firmware signatures for the model
    And I build custom_VARS.fd for the model
    And I boot the guest image with the model's firmware
    Then the VM should exit successfully

    Examples: Hardware models
      | model |
