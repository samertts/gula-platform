import WidgetKit
import SwiftUI
import CoreData

struct PendingOrdersProvider: TimelineProvider {
    func placeholder(in context: Context) -> PendingOrdersEntry {
        PendingOrdersEntry(date: Date(), pendingOrders: 5, criticalResults: 2, pendingSamples: 3)
    }

    func getSnapshot(in context: Context, completion: @escaping (PendingOrdersEntry) -> Void) {
        let entry = loadCurrentData()
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<PendingOrdersEntry>) -> Void) {
        let entry = loadCurrentData()
        let nextUpdate = Calendar.current.date(byAdding: .minute, value: 15, to: Date()) ?? Date()
        let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
        completion(timeline)
    }

    private func loadCurrentData() -> PendingOrdersEntry {
        let context = CoreDataStack.shared.viewContext

        let fetchPendingOrders: NSFetchRequest<NSFetchRequestResult> = OrderEntity.fetchRequest()
        fetchPendingOrders.predicate = NSPredicate(format: "status != %@ AND status != %@", "completed", "cancelled")
        fetchPendingOrders.resultType = .countResultType
        let pendingOrders = (try? context.count(for: fetchPendingOrders as! NSFetchRequest<OrderEntity>)) ?? 0

        let fetchCritical: NSFetchRequest<NSFetchRequestResult> = ResultEntity.fetchRequest()
        fetchCritical.predicate = NSPredicate(format: "isCritical == YES AND status != %@", "verified")
        fetchCritical.resultType = .countResultType
        let criticalResults = (try? context.count(for: fetchCritical as! NSFetchRequest<ResultEntity>)) ?? 0

        let fetchPendingSamples: NSFetchRequest<NSFetchRequestResult> = SampleEntity.fetchRequest()
        fetchPendingSamples.predicate = NSPredicate(format: "status == %@", "collected")
        fetchPendingSamples.resultType = .countResultType
        let pendingSamples = (try? context.count(for: fetchPendingSamples as! NSFetchRequest<SampleEntity>)) ?? 0

        return PendingOrdersEntry(
            date: Date(),
            pendingOrders: pendingOrders,
            criticalResults: criticalResults,
            pendingSamples: pendingSamples
        )
    }
}

struct PendingOrdersEntry: TimelineEntry {
    let date: Date
    let pendingOrders: Int
    let criticalResults: Int
    let pendingSamples: Int
}

struct GulaWidgetEntryView: View {
    var entry: PendingOrdersEntry
    @Environment(\.locale) var locale
    @Environment(\.widgetFamily) var family

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            HStack {
                Image(systemName: "cross.case.fill")
                    .foregroundColor(.gulaPrimary)
                Text("app_name".localized)
                    .gulaTitleSmall()
                    .fontWeight(.bold)
                    .foregroundColor(.gulaPrimary)
                Spacer()
            }

            if family == .systemSmall {
                compactContent
            } else {
                expandedContent
            }
        }
        .padding()
        .background(Color.gulaSurfacePrimary)
    }

    private var compactContent: some View {
        VStack(spacing: DesignTokens.Spacing.xs) {
            HStack {
                Image(systemName: "list.clipboard")
                    .foregroundColor(.gulaInfo)
                    .font(.caption)
                Text("\(entry.pendingOrders)")
                    .gulaTitleMedium()
                    .fontWeight(.bold)
                Spacer()
            }

            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.gulaCritical)
                    .font(.caption)
                Text("\(entry.criticalResults)")
                    .gulaTitleMedium()
                    .fontWeight(.bold)
                Spacer()
            }

            HStack {
                Image(systemName: "testtube.2")
                    .foregroundColor(.gulaAccent)
                    .font(.caption)
                Text("\(entry.pendingSamples)")
                    .gulaTitleMedium()
                    .fontWeight(.bold)
                Spacer()
            }
        }
    }

    private var expandedContent: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            WidgetRow(icon: "list.clipboard", color: .gulaInfo, title: "orders".localized, count: entry.pendingOrders)
            WidgetRow(icon: "exclamationmark.triangle.fill", color: .gulaCritical, title: "critical".localized, count: entry.criticalResults)
            WidgetRow(icon: "testtube.2", color: .gulaAccent, title: "samples".localized, count: entry.pendingSamples)
        }
    }
}

struct WidgetRow: View {
    let icon: String
    let color: Color
    let title: String
    let count: Int

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 24)
            Text(title)
                .gulaLabelMedium()
                .foregroundColor(.gulaTextSecondary)
            Spacer()
            Text("\(count)")
                .gulaTitleSmall()
                .fontWeight(.bold)
                .foregroundColor(.gulaTextPrimary)
        }
    }
}

struct GulaWidget: Widget {
    let kind: String = "com.gula.widget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: PendingOrdersProvider()) { entry in
            GulaWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("GULA Widget")
        .description("widget_description".localized)
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
