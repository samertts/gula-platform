export type OrderStatus = "معلق" | "قيد التنفيذ" | "مكتمل";

export type LabOrder = {
  id: string;
  patient: string;
  test: string;
  physician: string;
  receivedAt: string;
  status: OrderStatus;
  priority: "عادي" | "عاجل";
};

export function filterOrders(list: LabOrder[], query: string, status: "الكل" | OrderStatus) {
  const normalizedQuery = query.trim().toLocaleLowerCase("ar");
  return list.filter((order) => {
    const matchesStatus = status === "الكل" || order.status === status;
    const matchesQuery = !normalizedQuery || [order.id, order.patient, order.test, order.physician]
      .join(" ")
      .toLocaleLowerCase("ar")
      .includes(normalizedQuery);
    return matchesStatus && matchesQuery;
  });
}

export function nextMobileSidebarState(isOpen: boolean) {
  return !isOpen;
}
