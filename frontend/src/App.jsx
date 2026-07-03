import { useState, useEffect, useCallback } from "react";
import "./App.css";

const API_BASE = "/api/endpoints";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}


async function settingsApi(path, options = {}) {
  const res = await fetch(`/api/settings${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function EndpointForm({ endpoint, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    route_name: "",
    instance_id: "",
    app_id: "",
    description: "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (endpoint) {
      setForm({
        route_name: endpoint.route_name,
        instance_id: endpoint.instance_id,
        app_id: endpoint.app_id,
        description: endpoint.description,
      });
    }
  }, [endpoint]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!endpoint && !/^[a-zA-Z0-9-]+$/.test(form.route_name)) {
      setError("路由名仅允许字母、数字和连字符");
      return;
    }
    if (!form.instance_id.trim() || !form.app_id.trim()) {
      setError("Instance ID 和 App ID 不能为空");
      return;
    }
    setSaving(true);
    try {
      await onSubmit(form);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{endpoint ? "编辑端点" : "新增端点"}</h2>
        <form onSubmit={handleSubmit}>
          <label>
            路由名
            <input
              name="route_name"
              value={form.route_name}
              onChange={handleChange}
              disabled={!!endpoint}
              placeholder="例如: helpdesk"
              required
            />
          </label>
          <label>
            Instance ID
            <input
              name="instance_id"
              value={form.instance_id}
              onChange={handleChange}
              placeholder="例如: udvmkl6c41hs"
              required
            />
          </label>
          <label>
            App ID
            <input
              name="app_id"
              value={form.app_id}
              onChange={handleChange}
              placeholder="例如: 1625"
              required
            />
          </label>
          <label>
            描述
            <input
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="可选描述"
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onCancel}>
              取消
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


function SettingsPanel({ settings, onSave, onClose }) {
  const [draft, setDraft] = useState({ ...settings });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (key, value) => {
    setDraft({ ...draft, [key]: value });
    setError("");
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      for (const [key, value] of Object.entries(draft)) {
        if (value !== settings[key]) {
          await onSave(key, value);
        }
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const labels = {
    wenxue_base_url: "问学平台基础地址",
  };
  const placeholders = {
    wenxue_base_url: "https://wenxue.example.com",
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>系统设置</h2>
        <div className="settings-fields">
          {Object.keys(draft).map((key) => (
            <label key={key}>
              {labels[key] || key}
              <input
                value={draft[key]}
                onChange={(e) => handleChange(key, e.target.value)}
                placeholder={placeholders[key] || ""}
              />
            </label>
          ))}
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="form-actions">
          <button className="btn-secondary" onClick={onClose}>取消</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}

function EndpointList({ endpoints, onEdit, onDelete }) {
  const [deleting, setDeleting] = useState(null);

  const handleDelete = async (ep) => {
    if (!window.confirm(`确定删除路由 "${ep.route_name}"？`)) return;
    setDeleting(ep.id);
    try {
      await onDelete(ep.id);
    } finally {
      setDeleting(null);
    }
  };

  if (endpoints.length === 0) {
    return (
      <div className="empty-state">
        <p>暂无端点配置</p>
        <p className="hint">点击上方"新增端点"按钮开始添加</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>路由名</th>
            <th>Instance ID</th>
            <th>App ID</th>
            <th>描述</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {endpoints.map((ep) => (
            <tr key={ep.id}>
              <td>
                <code>{ep.route_name}</code>
              </td>
              <td>
                <code>{ep.instance_id}</code>
              </td>
              <td>{ep.app_id}</td>
              <td className="desc-cell">{ep.description}</td>
              <td className="actions">
                <button
                  className="btn-icon"
                  title="编辑"
                  onClick={() => onEdit(ep)}
                >
                  ✏️
                </button>
                <button
                  className="btn-icon btn-danger"
                  title="删除"
                  onClick={() => handleDelete(ep)}
                  disabled={deleting === ep.id}
                >
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [endpoints, setEndpoints] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({});
  const [loadingSettings, setLoadingSettings] = useState(true);

  const fetchEndpoints = useCallback(async () => {
    try {
      const data = await api("");
      setEndpoints(data);
      setError("");
    } catch (err) {
      setError("加载配置失败: " + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await settingsApi("");
      const map = {};
      data.forEach((s) => {
        map[s.key] = s.value;
      });
      setSettings(map);
    } catch (err) {
      console.error("加载设置失败:", err);
    } finally {
      setLoadingSettings(false);
    }
  }, []);

  useEffect(() => {
    fetchEndpoints();
    fetchSettings();
  }, [fetchEndpoints, fetchSettings]);

  const handleAdd = async (form) => {
    await api("", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setShowForm(false);
    await fetchEndpoints();
  };

  const handleUpdate = async (form) => {
    await api(`/${editing.id}`, {
      method: "PUT",
      body: JSON.stringify(form),
    });
    setEditing(null);
    await fetchEndpoints();
  };

  const handleDelete = async (id) => {
    await api(`/${id}`, { method: "DELETE" });
    await fetchEndpoints();
  };

  const handleSettingSave = async (key, value) => {
    await settingsApi(`/${key}`, {
      method: "PUT",
      body: JSON.stringify({ value }),
    });
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-row">
          <div>
            <h1>问学飞书 SSO 桥接器</h1>
            <p className="subtitle">管理端点路由与飞书 SSO 跳转配置</p>
          </div>
          <button
            className="btn-icon btn-settings"
            title="系统设置"
            onClick={() => setShowSettings(true)}
          >
            ⚙️
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="toolbar">
          <button
            className="btn-primary"
            onClick={() => {
              setEditing(null);
              setShowForm(true);
            }}
          >
            + 新增端点
          </button>
          {error && <span className="toolbar-error">{error}</span>}
        </div>

        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <EndpointList
            endpoints={endpoints}
            onEdit={(ep) => {
              setEditing(ep);
              setShowForm(true);
            }}
            onDelete={handleDelete}
          />
        )}
      </main>

      {showForm && (
        <EndpointForm
          endpoint={editing}
          onSubmit={editing ? handleUpdate : handleAdd}
          onCancel={() => {
            setShowForm(false);
            setEditing(null);
          }}
        />
      )}

      {showSettings && !loadingSettings && (
        <SettingsPanel
          settings={settings}
          onSave={handleSettingSave}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

export default App;
