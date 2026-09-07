# Abu Dhabi Ladies Club — site, member app and staff console

Static, bilingual (EN/AR), generated from JSON by one Python script. No Node, no
framework, no build chain.

```bash
python3 adlc-web/build.py            # build into adlc-web/dist
python3 adlc-web/build.py --serve    # build, then serve ($PORT, default 8080)
```

Full documentation, conventions and the build guards are in
[`adlc-web/README.md`](adlc-web/README.md).

**Status:** unreleased client work. The mark is a reconstruction and must not
ship; prices, capacities, staff names and operational figures are sample data.
