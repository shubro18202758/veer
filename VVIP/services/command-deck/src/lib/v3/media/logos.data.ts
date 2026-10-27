/**
 * The agency and source marks on file (static/logos; generated from the curated redesign/v3/logos/manifest.json). Used
 * as-is: trimmed and resized only. `plate`: 'light' for a dark or transparent mark that needs a white plate on a dark
 * ground; 'dark' for a white mark that needs a dark plate on a light ground; 'none' for a mark that reads on both.
 */
import type { Mark } from './logos';

export const MARK_ROWS: readonly Mark[] = [
	{ key: 'gujarat_police', name: 'Gujarat Police', src: '/logos/gujarat-police.png', w: 99, h: 128, plate: 'none' },
	{ key: 'gujarat_police_badge', name: 'Gujarat Police (badge, no text)', src: '/logos/gujarat-police-badge.png', w: 98, h: 128, plate: 'none' },
	{ key: 'ahmedabad_city_police', name: 'Ahmedabad City Police', src: '/logos/ahmedabad-city-police.png', w: 175, h: 128, plate: 'none' },
	{ key: 'emri_108', name: 'EMRI Green Health Services (108 Emergency, Gujarat)', src: '/logos/emri-108.png', w: 275, h: 49, plate: 'light' },
	{ key: 'amc', name: 'Amdavad Municipal Corporation (AMC)', src: '/logos/amc.png', w: 125, h: 128, plate: 'light' },
	{ key: 'gsdma', name: 'Gujarat State Disaster Management Authority (GSDMA)', src: '/logos/gsdma.png', w: 600, h: 59, plate: 'light' },
	{ key: 'ndma', name: 'National Disaster Management Authority (NDMA)', src: '/logos/ndma.png', w: 126, h: 128, plate: 'none' },
	{ key: 'gmrc', name: 'Gujarat Metro Rail Corporation (GMRC) / Ahmedabad Metro', src: '/logos/gmrc.png', w: 96, h: 128, plate: 'none' },
	{ key: 'janmarg_brts', name: 'Ahmedabad Janmarg BRTS', src: '/logos/janmarg-brts.png', w: 116, h: 93, plate: 'none' },
	{ key: 'amts', name: 'Ahmedabad Municipal Transport Service (AMTS)', src: '/logos/amts.png', w: 124, h: 128, plate: 'light' },
	{ key: 'ndma_sachet', name: 'NDMA Sachet (National Disaster Alert Portal)', src: '/logos/ndma-sachet.png', w: 600, h: 52, plate: 'dark' },
	{ key: 'imd', name: 'India Meteorological Department (IMD)', src: '/logos/imd.png', w: 69, h: 128, plate: 'none' },
	{ key: 'gdelt', name: 'GDELT Project', src: '/logos/gdelt.png', w: 128, h: 128, plate: 'none' },
	{ key: 'google_news', name: 'Google News', src: '/logos/google-news.svg', w: 6551, h: 5360, plate: 'none' },
	{ key: 'reddit', name: 'Reddit', src: '/logos/reddit.svg', w: 72, h: 72, plate: 'none' },
	{ key: 'openstreetmap', name: 'OpenStreetMap', src: '/logos/openstreetmap.svg', w: 256, h: 256, plate: 'none' },
	{ key: 'cesium', name: 'Cesium (Cesium ion)', src: '/logos/cesium.svg', w: 512, h: 512, plate: 'none' },
];
