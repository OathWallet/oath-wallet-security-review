import Foundation
import CoreGraphics
import ImageIO

struct Raster: Encodable { let path: String; let format: String; let width: Int; let height: Int }
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let paths = try JSONDecoder().decode([String].self, from: FileHandle.standardInput.readDataToEndOfFile())
var rows = [Raster]()
for path in paths {
    try autoreleasepool {
        let url = root.appendingPathComponent(path)
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              CGImageSourceGetCount(source) == 1,
              let type = CGImageSourceGetType(source) as String?,
              type == (path.hasSuffix(".png") ? "public.png" : "public.jpeg"),
              let props = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let w = props[kCGImagePropertyPixelWidth] as? Int,
              let h = props[kCGImagePropertyPixelHeight] as? Int,
              (1...8192).contains(w), (1...8192).contains(h), w*h <= 16_777_216,
              let image = CGImageSourceCreateImageAtIndex(source,0,[kCGImageSourceShouldCacheImmediately:true] as CFDictionary),
              image.width == w, image.height == h else {
            throw NSError(domain: "BundledRaster", code: 1, userInfo: [NSLocalizedDescriptionKey:path])
        }
        rows.append(Raster(path:path,format:type,width:w,height:h))
    }
}
FileHandle.standardOutput.write(try JSONEncoder().encode(rows))
