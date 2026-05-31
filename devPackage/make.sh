#!/usr/bin/env bash
# ============================================================
#  build_deb.sh  –  Build the BlockMeshAuto .deb package
#  Run from the repo root:  bash build_deb.sh
# ============================================================

set -e  # Exit immediately on any error

#  Config 
PACKAGE_NAME="blockMeshAuto"
VERSION="2.1.1"
PKG_DIR="devPackage/${PACKAGE_NAME}-${VERSION}"
LIB_DEST="${PKG_DIR}/usr/lib/${PACKAGE_NAME}"
BIN_DEST="${PKG_DIR}/usr/bin"
SHARE_DEST="${PKG_DIR}/usr/share/applications"

#  Step 1: Clean any previous build artefacts 
echo ">>> Cleaning previous build..."
rm -rf "${LIB_DEST}"
find "${PKG_DIR}" -name "*.pyc" -delete
find "${PKG_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

#  Step 2: Create directory tree 
echo ">>> Creating directory structure..."
mkdir -p "${LIB_DEST}"
mkdir -p "${BIN_DEST}"
mkdir -p "${SHARE_DEST}"

# Ensure DEBIAN dir exists (it already should, but just in case)
mkdir -p "${PKG_DIR}/DEBIAN"

#  Step 3: Copy Python source into usr/lib 
echo ">>> Copying application code to ${LIB_DEST}..."
cp -r Code/* "${LIB_DEST}/"

# Remove any leftover temp / cache files from the copy
find "${LIB_DEST}" -name "*.pyc"      -delete
find "${LIB_DEST}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${LIB_DEST}" -name "*.json.bak"  -delete
find "${LIB_DEST}" -name "*.json.backup" -delete
# Remove the temp directory if it was copied in
rm -rf "${LIB_DEST}/temp"

echo "    Files copied."

#  Step 4: Write the launcher script 
echo ">>> Writing launcher to ${BIN_DEST}/${PACKAGE_NAME}..."
cat > "${BIN_DEST}/${PACKAGE_NAME}" << 'EOF'
#!/usr/bin/env bash
python3 /usr/lib/blockMeshAuto/main.py "$@"
EOF
chmod 0755 "${BIN_DEST}/${PACKAGE_NAME}"

#  Step 5: Write the .desktop entry 
echo ">>> Writing .desktop file..."
cat > "${SHARE_DEST}/${PACKAGE_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Version=${VERSION}
Name=BlockMeshAuto
Comment=GUI tool for OpenFOAM blockMesh generation
Path=/usr/lib/${PACKAGE_NAME}
Exec=${PACKAGE_NAME}
Icon=/usr/lib/${PACKAGE_NAME}/BlockMeshLogo.png
Terminal=false
Categories=Science;Engineering;
EOF

#  Step 6: Write / refresh the DEBIAN/control file 
echo ">>> Writing DEBIAN/control..."
# Count installed size in KB
INSTALLED_KB=$(du -sk "${LIB_DEST}" | awk '{print $1}')

cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Architecture: all
Maintainer: Chinmay S Patil <patil.chinmay3031@gmail.com>
Installed-Size: ${INSTALLED_KB}
Depends: python3 (>= 3.10), python3-tk, python3-numpy, python3-pil
Description: BlockMeshAuto – GUI for OpenFOAM blockMesh generation
 A professional dark-mode GUI that lets you define points, connections,
 hex blocks, curved edges, and boundary patches, then exports a valid
 OpenFOAM blockMeshDict file.
EOF

#  Step 7: Fix permissions (dpkg-deb is strict about these) 
echo ">>> Fixing permissions..."
find "${PKG_DIR}"        -type d -exec chmod 0755 {} \;
find "${PKG_DIR}"        -type f -exec chmod 0644 {} \;
chmod 0755 "${BIN_DEST}/${PACKAGE_NAME}"
chmod 0755 "${PKG_DIR}/DEBIAN"
# DEBIAN scripts must be executable if they exist
for script in postinst prerm postrm preinst; do
    [ -f "${PKG_DIR}/DEBIAN/${script}" ] && chmod 0755 "${PKG_DIR}/DEBIAN/${script}"
done

#  Step 8: Build the .deb 
echo ">>> Building .deb package..."
cd devPackage
dpkg-deb --build --root-owner-group "${PACKAGE_NAME}-${VERSION}"/
cd ..

DEB_FILE="devPackage/${PACKAGE_NAME}-${VERSION}.deb"
echo ""
echo "============================================"
echo "  Build complete!"
echo "  Package: ${DEB_FILE}"
echo "  Size:    $(du -sh "${DEB_FILE}" | awk '{print $1}')"
echo "============================================"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${DEB_FILE}"
echo ""
echo "To verify contents:"
echo "  dpkg-deb --contents ${DEB_FILE}"
echo ""
echo "To uninstall:"
echo "  sudo apt remove ${PACKAGE_NAME}"
