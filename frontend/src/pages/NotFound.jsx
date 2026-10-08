import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import Icon from "../components/Icon";

export default function NotFound() {
  return (
    <Layout title="Nicht gefunden">
      <div className="page">
        <div className="empty">
          <span className="empty-icon">
            <Icon name="search" size={22} />
          </span>
          <strong>Seite nicht gefunden</strong>
          <span>Diese Adresse gibt es nicht – oder du hast keinen Zugriff darauf.</span>
          <Link to="/" className="btn btn-primary" style={{ textDecoration: "none", marginTop: 8 }}>
            Zur Suche
          </Link>
        </div>
      </div>
    </Layout>
  );
}
