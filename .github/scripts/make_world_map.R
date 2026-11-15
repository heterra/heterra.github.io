#!/usr/bin/env Rscript
# Write assets/world-map.js: the outlines of the countries and regions for the map of the users section.
#
#   Rscript .github/scripts/make_world_map.R        (needs the R packages sf, rnaturalearth, rnaturalearthdata)
#
# Source: Natural Earth 1:50m "Admin 0 - Countries" (public domain), in the Equal Earth projection, without
# Antarctica. One outline per ISO 3166-1 alpha-2 code, the code Google Analytics gives as countryId; areas
# without a code of their own are drawn with the country whose code they carry (Somaliland with SO, Northern
# Cyprus with CY). Run again only to change the map; the numbers come from stats.json.
suppressPackageStartupMessages({ library(sf); library(rnaturalearth) })
sf_use_s2(FALSE)

width <- 2000          # the map's width in its own units; coordinates are whole numbers of these
tolerance <- 9000      # metres: about half a unit
small <- 14            # an outline less wide and less high than this many units also gets a dot, so it can be seen

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
out <- file.path(here, "..", "..", "assets", "world-map.js")

w <- ne_countries(scale = 50, returnclass = "sf")
w <- w[w$adm0_a3 != "ATA", ]
w$id <- w$iso_a2_eh
w$id[w$name == "Somaliland"] <- "SO"
w$id[w$name == "N. Cyprus"] <- "CY"
w <- w[!is.na(w$id) & w$id != "-99", c("id", "name")]
w <- st_transform(st_make_valid(w), "+proj=eqearth +lon_0=0 +datum=WGS84 +units=m")
w <- aggregate(w["id"], by = list(code = w$id), FUN = function(x) x[1])
w <- st_simplify(w, preserveTopology = TRUE, dTolerance = tolerance)
w <- w[!st_is_empty(w), ]

box <- st_bbox(w)
k <- width / (box[["xmax"]] - box[["xmin"]])
height <- ceiling((box[["ymax"]] - box[["ymin"]]) * k)
X <- function(x) round((x - box[["xmin"]]) * k)
Y <- function(y) round((box[["ymax"]] - y) * k)

ring <- function(m) {
  p <- cbind(X(m[, 1]), Y(m[, 2]))
  p <- p[c(TRUE, rowSums(abs(diff(p))) > 0), , drop = FALSE]      # points that fall on the one before
  if (nrow(p) < 3) return("")
  # the first point absolute, the others as steps: shorter text
  d <- diff(p)
  paste0("M", p[1, 1], ",", p[1, 2], "l", paste(d[, 1], d[, 2], sep = ",", collapse = " "), "z")
}
shapes <- character(0)
dots <- character(0)
for (i in seq_len(nrow(w))) {
  g <- st_geometry(w)[[i]]
  polys <- if (inherits(g, "MULTIPOLYGON")) unclass(g) else list(unclass(g))
  d <- paste(unlist(lapply(polys, function(p) vapply(p, ring, ""))), collapse = "")
  b <- st_bbox(g)
  tiny <- (b[["xmax"]] - b[["xmin"]]) * k < small && (b[["ymax"]] - b[["ymin"]]) * k < small
  if (nchar(d) == 0 && !tiny) next
  shapes <- c(shapes, sprintf('"%s":"%s"', w$code[i], d))
  if (tiny) {
    c0 <- st_coordinates(st_centroid(st_geometry(w)[i]))
    dots <- c(dots, sprintf('"%s":[%d,%d]', w$code[i], X(c0[1]), Y(c0[2])))
  }
}
text <- paste0(
  "// Written by .github/scripts/make_world_map.R from Natural Earth 1:50m (public domain); not edited by hand.\n",
  "window.heterraWorld = {\"width\":", width, ",\"height\":", height,
  ",\n\"shapes\":{\n", paste(shapes, collapse = ",\n"), "\n},\n\"dots\":{", paste(dots, collapse = ","), "}};\n")
writeLines(text, out, sep = "", useBytes = TRUE)
cat(length(shapes), "outlines,", length(dots), "with a dot,", width, "x", height, ",", file.size(out), "bytes\n")
