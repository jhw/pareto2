"""
infra:
  api:
    userpool:
      attributes:
      - name: foo
        type: str
        value: bar
  bucket:
    public: false
  builder: {}
  queue: 
    batch-size: 10
  table:
    batch-window: 1
    indexes:
    - name: foobar
      type: S
"""
