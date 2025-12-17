-- ojs-offline.lua
-- Quarto filter to inject offline Observable JS dependencies

local has_ojs = false

-- Check for OJS content in code blocks
function CodeBlock(el)
  if el.classes:includes("ojs") or el.classes:includes("{ojs}") then
    has_ojs = true
  end
  return el
end

-- Check for OJS divs
function Div(el)
  if el.classes:includes("ojs-cell") or
     el.classes:includes("ojs") or
     el.attributes["ojs-define"] then
    has_ojs = true
  end
  return el
end

-- Inject dependencies at the Meta stage (after document is processed)
function Meta(meta)
  if has_ojs then
    -- Add the offline resolver script
    -- This MUST load before quarto-ojs-runtime.js
    quarto.doc.add_html_dependency({
      name = 'ojs-offline-resolver',
      version = '1.0.0',
      scripts = {
        {
          path = 'resources/ojs-offline-resolver.js',
          attribs = { type = 'module' }
        }
      },
      stylesheets = {}
    })

    -- Add the dependency map as a separate resource
    quarto.doc.add_html_dependency({
      name = 'ojs-offline-dependency-map',
      version = '1.0.0',
      scripts = {
        {
          path = 'resources/dependency-map.json',
          attribs = { type = 'application/json', id = 'ojs-dependency-map' }
        }
      }
    })

    -- Note: The actual library files will be accessed on-demand
    -- via the resolver when modules are imported
  end

  return meta
end

-- Return in the correct order for Pandoc
return {
  { CodeBlock = CodeBlock, Div = Div },
  { Meta = Meta }
}
