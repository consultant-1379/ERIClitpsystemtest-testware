Any "*.conf" files in the "src/tag_confs" directory will be included in the
RPM, and installed in /usr/local/etc/deploytag_confs.

Place any plugin configurations, as a stringified dictionary, required to be used
by the plugin, in this directory as "<model_item_id.conf>" so that the model will
use said configurations. See "example.conf".

The filename must match the model item id (i.e. ../package_1 == package_1.conf).
