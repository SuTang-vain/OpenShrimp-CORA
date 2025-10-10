import React, { useMemo, useState } from 'react'

type JSONSchema = {
  type: string
  properties?: Record<string, any>
  required?: string[]
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

  const renderField = (key: string, fieldSchema: any) => {
    const label = fieldSchema?.title || key
    const description = fieldSchema?.description
    const isRequired = required.includes(key)
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
            value={values[key] ?? ''}
            onChange={(e) => updateValue(key, e.target.value)}
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
            value={values[key] ?? 0}
            onChange={(e) => updateValue(key, e.target.value === '' ? '' : Number(e.target.value))}
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
            checked={Boolean(values[key])}
            onChange={(e) => updateValue(key, e.target.checked)}
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
            value={Array.isArray(values[key]) ? values[key].join(',') : ''}
            onChange={(e) => updateValue(key, e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
          />
        </div>
      )
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
          value={values[key] ?? ''}
          onChange={(e) => updateValue(key, e.target.value)}
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

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
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