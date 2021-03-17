"""rio_tiler.main: raster processing."""

import mercantile
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds

from rio_tiler import utils
from rio_tiler.errors import TileOutsideBounds

dst_crs = CRS.from_wkt('PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System_Jednotne_Trigonometricke_Site_Katastralni",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[589,76,480,0,0,0,0],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak"],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.83333333333333],PARAMETER["azimuth",30.28813972222222],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]')

def bounds(address):
    """
    Retrieve image bounds.

    Attributes
    ----------
    address : str
        file url.

    Returns
    -------
    out : dict
        dictionary with image bounds.

    """
    with rasterio.open(address) as src:
        bounds = transform_bounds(src.crs, dst_crs, *src.bounds, densify_pts=21)

    return {"url": address, "bounds": list(bounds)}


def metadata(address, pmin=2, pmax=98, **kwargs):
    """
    Return image bounds and band statistics.

    Attributes
    ----------
    address : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.
    pmin : int, optional, (default: 2)
        Histogram minimum cut.
    pmax : int, optional, (default: 98)
        Histogram maximum cut.
    kwargs : optional
        These are passed to 'rio_tiler.utils.raster_get_stats'
        e.g: overview_level=2, dst_crs='epsg:5514'

    Returns
    -------
    out : dict
        Dictionary with image bounds and bands statistics.

    """
    info = {"address": address}
    info.update(utils.raster_get_stats(address, percentiles=(pmin, pmax), **kwargs))
    return info


def tile(address, tile_x, tile_y, tile_z, tilesize=256, **kwargs):
    """
    Create mercator tile from any images.

    Attributes
    ----------
    address : str
        file url.
    tile_x : int
        Mercator tile X index.
    tile_y : int
        Mercator tile Y index.
    tile_z : int
        Mercator tile ZOOM level.
    tilesize : int, optional (default: 256)
        Output image size.
    kwargs: dict, optional
        These will be passed to the 'rio_tiler.utils._tile_read' function.

    Returns
    -------
    data : numpy ndarray
    mask: numpy array

    """
    with rasterio.open(address) as src:
        bounds = transform_bounds(src.crs, dst_crs, *src.bounds, densify_pts=21)

        if not utils.tile_exists(bounds, tile_z, tile_x, tile_y):
            raise TileOutsideBounds(
                "Tile {}/{}/{} is outside image bounds".format(tile_z, tile_x, tile_y)
            )

        mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)
        return utils.tile_read(src, tile_bounds, tilesize, **kwargs)
