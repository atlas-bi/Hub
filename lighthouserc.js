module.exports = {
  ci: {
    upload: {
      target: 'lhci',
      serverBaseUrl: 'https://lighthouse.atlas.bi',
    },
    // "assert": {
    //   "preset": "lighthouse:no-pwa",
    //   "assertions": {
    //     "color-contrast": "warn",
    //     "is-crawlable": "off",
    //     "redirects": "off",
    //     "robots-txt": "off",
    //     "csp-xss": "warn",
    //     "unused-css-rules": "warn",
    //     "tap-targets": "warn",
    //     "third-party-facades": "warn",
    //     "unused-javascript": "warn",
    //     "uses-responsive-images": "warn",
    //     "uses-text-compression": "warn",
    //     "crawlable-anchors": "warn",
    //     "label": "warn",
    //     "link-name": "warn",
    //     "heading-order": "warn"
    //   },
    // },
    collect: {
      startServerCommand: "export FLASK_ENV=test && export FLASK_DEBUG=False && export FLASK_APP=web && export FLASK_RUN_PORT=4998 && poetry run flask run",
      url: [
        'http://localhost:4998',
        'http://localhost:4998/admin',
        'http://localhost:4998/connection',
        'http://localhost:4998/dashboard',
        'http://localhost:4998/project',
        'http://localhost:4998/task',
      ],
      maxAutodiscoverUrls: 10,
      settings: {
        hostname: '127.0.0.1'
      },
    },
  },
};
