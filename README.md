# organicBuildingMC

Based on [Organic Building Generation in Minecraft](https://arxiv.org/pdf/1906.05094).

Run locally without Minecraft or Minescript to print the floorplan and building layers:

```sh
python3 mainLogic.py 10 10 --debug --height 4
```

The first two arguments are length and width. Currently, generation places room seeds only.
