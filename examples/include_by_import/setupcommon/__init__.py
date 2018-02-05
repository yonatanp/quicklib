import os

hostname = os.getenv("HOSTNAME", "unknown")

setup_describe_hostname = {
    'setup': {
        'description': 'this package was built on %s' % hostname,
    }
}
