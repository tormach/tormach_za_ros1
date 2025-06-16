import QtQuick
import QtQuick.Layouts

Item {
  id: root

  ColumnLayout {
    anchors.centerIn: parent
    Text {
      text: {
        switch (GraphicsInfo.api) {
        case GraphicsInfo.Unknown:
          return "unknown";
        case GraphicsInfo.Software:
          return "Software";
        case GraphicsInfo.OpenGL:
          return "OpenGL";
        case GraphicsInfo.Direct3D12:
          return "Direct3D12";
        default:
          return "";
        }
      }
    }
    Text {
      text: GraphicsInfo.majorVersion + "." + GraphicsInfo.minorVersion
    }
    Text {
      text: {
        switch (GraphicsInfo.profile) {
        case GraphicsInfo.OpenGLNoProfile:
          return "No profile";
        case GraphicsInfo.OpenGLCoreProfile:
          return "Core profile";
        case GraphicsInfo.OpenGLCompatibilityProfile:
          return "Compatibility profile";
        default:
          return "";
        }
      }
    }
    Text {
      text: {
        switch (GraphicsInfo.renderableType) {
        case GraphicsInfo.SurfaceFormatUnspecified:
          return "Surface format unspecified";
        case GraphicsInfo.SurfaceFormatOpenGL:
          return "Surface format OpenGL";
        case GraphicsInfo.SurfaceFormatOpenGLES:
          return "Surface format OpenGLES";
        default:
          return "";
        }
      }
    }
    Text {
      text: {
        switch (GraphicsInfo.shaderCompilationType) {
        case GraphicsInfo.RuntimeCompilation:
          return "Shader runtime compilation";
        case GraphicsInfo.OfflineCompilation:
          return "Shader offline compilation";
        default:
          return "";
        }
      }
    }
    Text {
      text: {
        var output = "";
        var sourceType = GraphicsInfo.shaderSourceType;
        output += (sourceType & GraphicsInfo.ShaderSourceString) ? "Shader source string\n" : "";
        output += (sourceType & GraphicsInfo.ShaderSourceFile) ? "Shader source file\n" : "";
        output += (sourceType & GraphicsInfo.ShaderByteCode) ? "Shader byte code\n" : "";
        return output.trim();
      }
    }
    Text {
      text: {
        switch (GraphicsInfo.shaderType) {
        case GraphicsInfo.UnknownShadingLanguage:
          return "Unknown shading language";
        case GraphicsInfo.GLSL:
          return "GLSL";
        case GraphicsInfo.HLSL:
          return "HLSL";
        default:
          return "";
        }
      }
    }
  }
}
