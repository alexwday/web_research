# SSL Certificate

Place your `rbc-ca-bundle.cer` file in this directory.

The test script will automatically find it and use it for SSL connections.

## To get the certificate:

1. Copy from your iris-project:
   ```bash
   cp /path/to/iris-project/iris/src/initial_setup/rbc-ca-bundle.cer ./ssl_certs/
   ```

2. Or get it from your IT department

## File should be named:
```
ssl_certs/rbc-ca-bundle.cer
```