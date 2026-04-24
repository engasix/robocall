import { useLoaderData, useNavigate, useSearchParams } from "react-router";
import { boundary } from "@shopify/shopify-app-react-router/server";
import { authenticate } from "../shopify.server";
import db from "../db.server";

const PAGE_SIZE = 20;

const STATUS_LABELS = {
  pending:     "Pending",
  confirmed:   "Confirmed",
  cancelled:   "Cancelled",
  no_response: "No Response",
};

const STATUS_TONES = {
  pending:     "attention",
  confirmed:   "success",
  cancelled:   "critical",
  no_response: "warning",
};

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-PK", {
    day:    "2-digit",
    month:  "short",
    year:   "numeric",
    hour:   "2-digit",
    minute: "2-digit",
  });
}

function formatAmount(amount) {
  return `PKR ${Number(amount).toLocaleString("en-PK")}`;
}

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const settings = await db.settings.findUnique({ where: { shop } });

  if (!settings?.apiKey) {
    return { orders: [], total: 0, page: 1, pageSize: PAGE_SIZE, noApiKey: true, error: null };
  }

  const url = new URL(request.url);
  const page = Math.max(1, parseInt(url.searchParams.get("page") || "1", 10));

  try {
    const apiUrl = `${process.env.API_URL}/orders?page=${page}&page_size=${PAGE_SIZE}`;
    const response = await fetch(apiUrl, {
      headers: { "X-Api-Key": settings.apiKey },
    });

    if (!response.ok) {
      const text = await response.text();
      return { orders: [], total: 0, page, pageSize: PAGE_SIZE, noApiKey: false, error: `API error ${response.status}: ${text}` };
    }

    const json = await response.json();
    const { orders, total, page: currentPage, page_size } = json.data;
    return { orders, total, page: currentPage, pageSize: page_size, noApiKey: false, error: null };
  } catch (err) {
    return { orders: [], total: 0, page, pageSize: PAGE_SIZE, noApiKey: false, error: `Could not connect to ConfirmOye API: ${err.message}` };
  }
};

export default function Index() {
  const { orders, total, page, pageSize, noApiKey, error } = useLoaderData();
  const navigate = useNavigate();
  const [, setSearchParams] = useSearchParams();

  const totalPages = Math.ceil(total / pageSize);

  if (noApiKey) {
    return (
      <s-page heading="Orders">
        <s-section heading="Setup required">
          <s-paragraph>
            You need to configure your API key before orders can be tracked.
          </s-paragraph>
          <s-button onClick={() => navigate("/app/settings")}>
            Go to Settings
          </s-button>
        </s-section>
      </s-page>
    );
  }

  return (
    <s-page heading="Orders">
      {error && (
        <s-section>
          <s-banner tone="critical" heading="Error">{error}</s-banner>
        </s-section>
      )}

      {!error && orders.length === 0 && (
        <s-section heading="No orders yet">
          <s-paragraph>
            Orders will appear here once customers start placing COD orders.
          </s-paragraph>
        </s-section>
      )}

      {!error && orders.length > 0 && (
        <s-section>
          <s-table>
            <s-table-header-row>
              <s-table-header>Order #</s-table-header>
              <s-table-header>Customer</s-table-header>
              <s-table-header>Phone</s-table-header>
              <s-table-header>Amount</s-table-header>
              <s-table-header>Attempts</s-table-header>
              <s-table-header>Status</s-table-header>
              <s-table-header>Date</s-table-header>
            </s-table-header-row>
            <s-table-body>
              {orders.map((order) => (
                <s-table-row key={order.order_id}>
                  <s-table-cell>
                    {order.order_number ? `#${order.order_number}` : `ID ${order.order_id}`}
                  </s-table-cell>
                  <s-table-cell>{order.customer_name}</s-table-cell>
                  <s-table-cell>{order.phone}</s-table-cell>
                  <s-table-cell>{formatAmount(order.order_amount)}</s-table-cell>
                  <s-table-cell>{order.call_attempts ?? 0}</s-table-cell>
                  <s-table-cell>
                    <s-badge tone={STATUS_TONES[order.status] ?? "attention"}>
                      {STATUS_LABELS[order.status] ?? order.status}
                    </s-badge>
                  </s-table-cell>
                  <s-table-cell>{formatDate(order.created_at)}</s-table-cell>
                </s-table-row>
              ))}
            </s-table-body>
          </s-table>

          {totalPages > 1 && (
            <s-stack direction="inline" gap="base" align-items="center" style={{ marginTop: "16px" }}>
              <s-button
                disabled={page <= 1}
                onClick={() => setSearchParams({ page: String(page - 1) })}
              >
                Previous
              </s-button>
              <s-text>Page {page} of {totalPages} ({total} orders)</s-text>
              <s-button
                disabled={page >= totalPages}
                onClick={() => setSearchParams({ page: String(page + 1) })}
              >
                Next
              </s-button>
            </s-stack>
          )}
        </s-section>
      )}
    </s-page>
  );
}

export const headers = (headersArgs) => {
  return boundary.headers(headersArgs);
};
