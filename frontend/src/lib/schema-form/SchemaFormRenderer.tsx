import React, { useMemo, useState } from 'react'

type JSONSchema = {
  type: string
  properties?: Record<string, any>
  required?: string[]
  oneOf?: any[]
  anyOf?: any[]
}

interface SchemaFormRendererProps {
  schema: JSONSchema
  defaultValues?: Record<string, any>
  onSubmit: (values: Record<string, any>) => void
  submitLabel?: string
}

function getDefaultValueForField(fieldSchema: any) {
  if (fieldSchema?.default !== undefined) return fieldSchema.default
  const t = fieldSchema?.type
  if (t === 'string') return ''
  if (t === 'integer' || t === 'number') return 0
  if (t === 'boolean') return false
  if (t === 'array') return []
  if (t === 'object') return {}
  return ''
}

export const SchemaFormRenderer: React.FC<SchemaFormRendererProps> = ({
  schema,
  defaultValues,
  onSubmit,
  submitLabel = '执行工具',
}) => {
  const properties = useMemo(() => schema?.properties || {}, [schema])
  const required = useMemo(() => schema?.required || [], [schema])
  const oneOf = useMemo(() => schema?.oneOf || [], [schema])
  const anyOf = useMemo(() => schema?.anyOf || [], [schema])

  const initialValues = useMemo(() => {
    const v: Record<string, any> = {}
    Object.entries(properties).forEach(([key, p]) => {
      if (defaultValues && key in defaultValues) v[key] = defaultValues[key]
      else v[key] = getDefaultValueForField(p)
    })
    return v
  }, [properties, defaultValues])

  const [values, setValues] = useState<Record<string, any>>(initialValues)

  const updateValue = (key: string, val: any) => {
    setValues((prev) => ({ ...prev, [key]: val }))
  }

  const renderObject = (key: string, fieldSchema: any) => {
    const subs: Record<string, any> = fieldSchema?.properties || {}
    return (
      <div className="mb-4 border rounded p-3" key={key}>
        <div className="text-sm font-medium mb-2">{fieldSchema?.title || key}</div>
        {fieldSchema?.description ? (
          <p className="text-xs text-muted-foreground mb-2">{fieldSchema.description}</p>
        ) : null}
        {Object.entries(subs).map(([sk, ss]) => renderField(`${key}.${sk}`, ss, key))}
      </div>
    )
  }

  const getValueByKeyPath = (obj: any, keyPath: string) => {
    return keyPath.split('.').reduce((acc, k) => (acc ? acc[k] : undefined), obj)
  }

  const setValueByKeyPath = (obj: any, keyPath: string, val: any) => {
    const ks = keyPath.split('.')
    const last = ks.pop() as string
    let cur = obj
    for (const k of ks) {
      if (typeof cur[k] !== 'object' || cur[k] === null) cur[k] = {}
      cur = cur[k]
    }
    cur[last] = val
  }

  const renderField = (key: string, fieldSchema: any, parentKey?: string) => {
    const label = fieldSchema?.title || key
    const description = fieldSchema?.description
    const rootKey = parentKey ? parentKey : undefined
    const isRequired = required.includes(key) || (rootKey ? required.includes(rootKey) : false)
    const type = fieldSchema?.type
    const enumVals: any[] | undefined = fieldSchema?.enum

    const commonLabel = (
      <label className="block text-sm font-medium mb-1" htmlFor={key}>
        {label}{isRequired ? ' *' : ''}
      </label>
    )

    const commonDesc = description ? (
      <p className="text-xs text-muted-foreground mb-2">{description}</p>
    ) : null

    if (enumVals && Array.isArray(enumVals)) {
      return (
        <div className="mb-4" key={key}>
          {commonLabel}
          {commonDesc}
          <select
            id={key}
            className="w-full border rounded px-2 py-2 bg-background"
            value={getValueByKeyPath(values, key) ?? ''}
            onChange={(e) => {
              const v = e.target.value
              setValues((prev) => {
                const next = { ...prev }
                setValueByKeyPath(next, key, v)
                return next
              })
            }}
          >
            {enumVals.map((opt) => (
              <option key={`${key}-${opt}`} value={opt}>
                {String(opt)}
              </option>
            ))}
          </select>
        </div>
      )
    }

    if (type === 'integer' || type === 'number') {
      return (
        <div className="mb-4" key={key}>
          {commonLabel}
          {commonDesc}
          <input
            id={key}
            type="number"
            className="w-full border rounded px-2 py-2 bg-background"
            value={getValueByKeyPath(values, key) ?? 0}
            onChange={(e) => {
              const num = e.target.value === '' ? '' : Number(e.target.value)
              setValues((prev) => {
                const next = { ...prev }
                setValueByKeyPath(next, key, num)
                return next
              })
            }}
          />
        </div>
      )
    }

    if (type === 'boolean') {
      return (
        <div className="mb-4 flex items-center gap-2" key={key}>
          <input
            id={key}
            type="checkbox"
            checked={Boolean(getValueByKeyPath(values, key))}
            onChange={(e) => {
              const checked = e.target.checked
              setValues((prev) => {
                const next = { ...prev }
                setValueByKeyPath(next, key, checked)
                return next
              })
            }}
          />
          {commonLabel}
        </div>
      )
    }

    if (type === 'array') {
      return (
        <div className="mb-4" key={key}>
          {commonLabel}
          {commonDesc}
          <textarea
            id={key}
            className="w-full border rounded px-2 py-2 bg-background"
            placeholder="以逗号分隔的数组元素"
            value={(() => {
              const v = getValueByKeyPath(values, key)
              return Array.isArray(v) ? v.join(',') : ''
            })()}
            onChange={(e) => {
              const arr = e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
              setValues((prev) => {
                const next = { ...prev }
                setValueByKeyPath(next, key, arr)
                return next
              })
            }}
          />
        </div>
      )
    }

    if (type === 'object') {
      return renderObject(key, fieldSchema)
    }

    // 默认作为字符串处理
    return (
      <div className="mb-4" key={key}>
        {commonLabel}
        {commonDesc}
        <input
          id={key}
          type="text"
          className="w-full border rounded px-2 py-2 bg-background"
          value={getValueByKeyPath(values, key) ?? ''}
          onChange={(e) => {
            const text = e.target.value
            setValues((prev) => {
              const next = { ...prev }
              setValueByKeyPath(next, key, text)
              return next
            })
          }}
        />
      </div>
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // 简单校验：必填项不能为空
    for (const k of required) {
      if (values[k] === undefined || values[k] === null || values[k] === '') {
        alert(`字段 ${k} 为必填项`)
        return
      }
    }
    onSubmit(values)
  }

  const renderVariants = () => {
    const variants = oneOf.length > 0 ? oneOf : anyOf
    if (!variants || variants.length === 0) return null
    return (
      <div className="mb-4">
        <div className="text-sm font-medium mb-2">选择变体</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {variants.map((variant, idx) => (
            <button
              key={`variant-${idx}`}
              type="button"
              className="border rounded p-2 text-left hover:bg-accent"
              onClick={() => {
                // 切换到该变体的默认值
                const props = variant?.properties || {}
                const next: Record<string, any> = { ...values }
                Object.entries(props).forEach(([k, p]) => {
                  setValueByKeyPath(next, k, getDefaultValueForField(p))
                })
                setValues(next)
              }}
            >
              <div className="text-sm font-medium">{variant?.title || `变体 ${idx + 1}`}</div>
              {variant?.description ? (
                <div className="text-xs text-muted-foreground">{variant.description}</div>
              ) : null}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {renderVariants()}
      {Object.entries(properties).map(([key, fs]) => renderField(key, fs))}

      <div className="mt-6">
        <button type="submit" className="px-3 py-2 rounded bg-primary text-primary-foreground border">
          {submitLabel}
        </button>
      </div>
    </form>
  )
}

export default SchemaFormRenderer