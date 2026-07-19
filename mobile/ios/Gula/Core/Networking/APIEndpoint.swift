import Foundation

enum APIEndpoint {
    case login
    case refreshToken
    case changePassword
    case registerDevice(token: String, platform: String)
    case getProfile

    case listPatients(page: Int, limit: Int, search: String?, gender: String?, status: String?)
    case getPatient(id: Int)
    case createPatient
    case updatePatient(id: Int)
    case deletePatient(id: Int)
    case searchPatients(query: String, page: Int, limit: Int)
    case patientHistory(id: Int)
    case patientByPhone(phone: String)
    case patientStats
    case patientActivity(page: Int, limit: Int)
    case convertGuest
    case bulkAssignLab
    case scanPatientCard

    case listOrders(page: Int, limit: Int, patientId: Int?, status: String?)
    case getOrder(id: Int)
    case createOrder
    case cancelOrder(id: Int)
    case analyzeResults
    case createBatchOrders

    case listSamples(page: Int, limit: Int, status: String?, type: String?)
    case getSample(id: Int)
    case createSample
    case updateSample(id: Int)
    case deleteSample(id: Int)
    case sampleStats
    case bulkRegisterSamples
    case receiveSample(id: Int)
    case rejectSample(id: Int)
    case lookupSampleByBarcode(barcode: String)
    case printSampleLabel(id: Int)
    case transferSample(id: Int)
    case sampleTimeline(id: Int)
    case sampleHistory(id: Int)

    case listResults(page: Int, limit: Int, patientId: Int?, status: String?, isCritical: Bool?)
    case getResult(id: Int)
    case createResult
    case updateResult(id: Int)
    case deleteResult(id: Int)
    case verifyResult(id: Int)
    case approveResult(id: Int)
    case validateResult(id: Int)
    case bulkCreateResults
    case autoValidate
    case amendResult(id: Int)
    case getAmendments(id: Int)
    case resultStats
    case flagCritical(id: Int)
    case generateReport(id: Int)
    case listReports(page: Int, limit: Int)
    case deviceSubmitResults
    case listDeviceResults(page: Int, limit: Int)

    case listNotifications(page: Int, limit: Int, read: Bool?, type: String?)
    case createNotification
    case markNotificationRead(id: Int)
    case markAllNotificationsRead
    case deleteNotification(id: Int)
    case notificationStats
    case getNotificationPreferences
    case updateNotificationPreferences
    case testNotificationChannel

    case dashboard
    case labDashboard(labId: Int)
    case stats
    case statsTrends
    case revenue

    case listLabUsers(page: Int, limit: Int)
    case createLabUser
    case updateLabUser(id: Int)
    case deleteLabUser(id: Int)

    case adminListUsers(page: Int, limit: Int)
    case adminGetUser(id: Int)
    case adminCreateUser
    case adminUpdateUser(id: Int)
    case adminDeleteUser(id: Int)
    case adminDeactivateUser(id: Int)
    case adminReactivateUser(id: Int)
    case adminChangeUserRole(id: Int)
    case adminListLabs(page: Int, limit: Int)
    case adminCreateLab
    case adminUpdateLab(id: Int)
    case adminDeleteLab(id: Int)
    case adminStats
    case adminServiceStatus

    case unknown(path: String)

    var path: String {
        switch self {
        case .login: return "/login"
        case .refreshToken: return "/auth/refresh"
        case .changePassword: return "/auth/change-password"
        case .registerDevice: return "/mobile/register-device"
        case .getProfile: return "/auth/me"

        case .listPatients: return "/patients"
        case .getPatient(let id): return "/patients/\(id)"
        case .createPatient: return "/patients"
        case .updatePatient(let id): return "/patients/\(id)"
        case .deletePatient(let id): return "/patients/\(id)"
        case .searchPatients: return "/patients/search"
        case .patientHistory(let id): return "/patients/\(id)/history"
        case .patientByPhone(let phone): return "/patients/phone/\(phone.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? phone)"
        case .patientStats: return "/patients/stats"
        case .patientActivity: return "/patients/activity"
        case .convertGuest: return "/patients/convert-guest"
        case .bulkAssignLab: return "/patients/bulk-assign-lab"
        case .scanPatientCard: return "/patient-card/scan"

        case .listOrders: return "/orders"
        case .getOrder(let id): return "/orders/\(id)"
        case .createOrder: return "/orders"
        case .cancelOrder(let id): return "/orders/\(id)/cancel"
        case .analyzeResults: return "/analyze"
        case .createBatchOrders: return "/batch/orders"

        case .listSamples: return "/samples"
        case .getSample(let id): return "/samples/\(id)"
        case .createSample: return "/samples"
        case .updateSample(let id): return "/samples/\(id)"
        case .deleteSample(let id): return "/samples/\(id)"
        case .sampleStats: return "/samples/stats"
        case .bulkRegisterSamples: return "/samples/bulk-register"
        case .receiveSample(let id): return "/samples/\(id)/receive"
        case .rejectSample(let id): return "/samples/\(id)/reject"
        case .lookupSampleByBarcode(let barcode): return "/samples/barcode/\(barcode.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? barcode)"
        case .printSampleLabel(let id): return "/samples/\(id)/print-label"
        case .transferSample(let id): return "/samples/\(id)/transfer"
        case .sampleTimeline(let id): return "/samples/\(id)/timeline"
        case .sampleHistory(let id): return "/samples/history/\(id)"

        case .listResults: return "/results"
        case .getResult(let id): return "/results/\(id)"
        case .createResult: return "/results"
        case .updateResult(let id): return "/results/\(id)"
        case .deleteResult(let id): return "/results/\(id)"
        case .verifyResult(let id): return "/results/\(id)/verify"
        case .approveResult(let id): return "/results/\(id)/approve"
        case .validateResult(let id): return "/results/\(id)/validate"
        case .bulkCreateResults: return "/results/bulk"
        case .autoValidate: return "/results/auto-validate"
        case .amendResult(let id): return "/results/\(id)/amend"
        case .getAmendments(let id): return "/results/\(id)/amendments"
        case .resultStats: return "/results/stats"
        case .flagCritical(let id): return "/results/\(id)/flag-critical"
        case .generateReport(let id): return "/results/\(id)/report"
        case .listReports: return "/results/reports"
        case .deviceSubmitResults: return "/device/results"
        case .listDeviceResults: return "/device-results"

        case .listNotifications: return "/notifications"
        case .createNotification: return "/notifications"
        case .markNotificationRead(let id): return "/notifications/\(id)/read"
        case .markAllNotificationsRead: return "/notifications/read-all"
        case .deleteNotification(let id): return "/notifications/\(id)"
        case .notificationStats: return "/notifications/stats"
        case .getNotificationPreferences: return "/notifications/preferences"
        case .updateNotificationPreferences: return "/notifications/preferences"
        case .testNotificationChannel: return "/notifications/test"

        case .dashboard: return "/dashboard"
        case .labDashboard(let id): return "/dashboard/lab/\(id)"
        case .stats: return "/stats"
        case .statsTrends: return "/stats/trends"
        case .revenue: return "/stats/revenue"

        case .listLabUsers: return "/lab/users"
        case .createLabUser: return "/lab/users"
        case .updateLabUser(let id): return "/lab/users/\(id)"
        case .deleteLabUser(let id): return "/lab/users/\(id)"

        case .adminListUsers: return "/admin/users"
        case .adminGetUser(let id): return "/admin/users/\(id)"
        case .adminCreateUser: return "/admin/users"
        case .adminUpdateUser(let id): return "/admin/users/\(id)"
        case .adminDeleteUser(let id): return "/admin/users/\(id)"
        case .adminDeactivateUser(let id): return "/admin/users/\(id)/deactivate"
        case .adminReactivateUser(let id): return "/admin/users/\(id)/reactivate"
        case .adminChangeUserRole(let id): return "/admin/users/\(id)/role"
        case .adminListLabs: return "/admin/labs"
        case .adminCreateLab: return "/admin/labs"
        case .adminUpdateLab(let id): return "/admin/labs/\(id)"
        case .adminDeleteLab(let id): return "/admin/labs/\(id)"
        case .adminStats: return "/admin/stats"
        case .adminServiceStatus: return "/admin/service-status"

        case .unknown(let path): return path
        }
    }

    var method: String {
        switch self {
        case .login, .refreshToken, .registerDevice, .createPatient, .convertGuest, .bulkAssignLab,
                .scanPatientCard, .createOrder, .cancelOrder, .analyzeResults, .createBatchOrders,
                .createSample, .bulkRegisterSamples, .receiveSample, .rejectSample, .transferSample,
                .createResult, .bulkCreateResults, .autoValidate, .amendResult, .generateReport,
                .flagCritical, .deviceSubmitResults, .createNotification, .testNotificationChannel,
                .createLabUser, .adminCreateUser, .adminCreateLab, .adminDeactivateUser,
                .adminReactivateUser, .adminChangeUserRole:
            return "POST"
        case .updatePatient, .updateSample, .updateResult, .verifyResult, .approveResult,
                .validateResult, .updateNotificationPreferences, .markNotificationRead,
                .markAllNotificationsRead, .updateLabUser, .adminUpdateUser, .adminUpdateLab:
            return "PUT"
        case .deletePatient, .deleteSample, .deleteResult, .deleteNotification, .deleteLabUser,
                .adminDeleteUser, .adminDeleteLab:
            return "DELETE"
        default:
            return "GET"
        }
    }

    var isIdempotent: Bool {
        switch method {
        case "GET", "PUT", "DELETE": return true
        default: return false
        }
    }
}
