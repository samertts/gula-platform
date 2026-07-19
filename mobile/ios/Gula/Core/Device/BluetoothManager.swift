import Foundation
import CoreBluetooth

enum BluetoothState {
    case unknown
    case resetting
    case unsupported
    case unauthorized
    case poweredOff
    case poweredOn
}

protocol BluetoothManagerDelegate: AnyObject {
    func didDiscoverDevice(_ device: BluetoothDevice)
    func didConnectToDevice(_ device: BluetoothDevice)
    func didDisconnectFromDevice(_ device: BluetoothDevice)
    func didReceiveData(_ data: Data, from device: BluetoothDevice)
    func bluetoothStateChanged(_ state: BluetoothState)
    func didEncounterError(_ error: Error)
}

struct BluetoothDevice: Identifiable, Equatable {
    let id: String
    let name: String
    let rssi: Int
    let peripheral: CBPeripheral
    var isConnected: Bool = false
}

class BluetoothManager: NSObject, ObservableObject {
    static let shared = BluetoothManager()

    @Published var isScanning = false
    @Published var discoveredDevices: [BluetoothDevice] = []
    @Published var connectedDevice: BluetoothDevice?
    @Published var bluetoothState: BluetoothState = .unknown
    @Published var receivedData: Data?

    weak var delegate: BluetoothManagerDelegate?

    private var centralManager: CBCentralManager!
    private var connectedPeripheral: CBPeripheral?
    private var characteristic: CBCharacteristic?

    private let serviceUUIDs: [CBUUID] = [
        CBUUID(string: "180D"),
        CBUUID(string: "180F"),
        CBUUID(string: "1810"),
        CBUUID(string: "FFF0")
    ]

    override private init() {
        super.init()
        centralManager = CBCentralManager(delegate: self, queue: .main)
    }

    func startScanning() {
        guard centralManager.state == .poweredOn else { return }
        discoveredDevices.removeAll()
        isScanning = true
        centralManager.scanForPeripherals(withServices: serviceUUIDs, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
        DispatchQueue.main.asyncAfter(deadline: .now() + 30) { [weak self] in
            self?.stopScanning()
        }
    }

    func stopScanning() {
        centralManager.stopScan()
        isScanning = false
    }

    func connect(to device: BluetoothDevice) {
        centralManager.connect(device.peripheral, options: nil)
    }

    func disconnect() {
        guard let peripheral = connectedPeripheral else { return }
        centralManager.cancelPeripheralConnection(peripheral)
    }

    func sendData(_ data: Data) {
        guard let peripheral = connectedPeripheral,
              let characteristic = characteristic else { return }
        peripheral.writeValue(data, for: characteristic, type: .withResponse)
    }

    func sendString(_ string: String) {
        guard let data = string.data(using: .utf8) else { return }
        sendData(data)
    }
}

extension BluetoothManager: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        let state: BluetoothState
        switch central.state {
        case .unknown: state = .unknown
        case .resetting: state = .resetting
        case .unsupported: state = .unsupported
        case .unauthorized: state = .unauthorized
        case .poweredOff: state = .poweredOff
        case .poweredOn: state = .poweredOn
        @unknown default: state = .unknown
        }

        DispatchQueue.main.async {
            self.bluetoothState = state
        }
        delegate?.bluetoothStateChanged(state)

        if state == .poweredOn {
            startScanning()
        }
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String: Any], rssi RSSI: NSNumber) {
        let deviceName = peripheral.name ?? advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? "Unknown Device"
        let device = BluetoothDevice(
            id: peripheral.identifier.uuidString,
            name: deviceName,
            rssi: RSSI.intValue,
            peripheral: peripheral
        )

        DispatchQueue.main.async {
            if !self.discoveredDevices.contains(where: { $0.id == device.id }) {
                self.discoveredDevices.append(device)
            }
        }
        delegate?.didDiscoverDevice(device)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.delegate = self
        connectedPeripheral = peripheral
        peripheral.discoverServices(serviceUUIDs)

        let device = BluetoothDevice(
            id: peripheral.identifier.uuidString,
            name: peripheral.name ?? "Connected Device",
            rssi: 0,
            peripheral: peripheral,
            isConnected: true
        )

        DispatchQueue.main.async {
            self.connectedDevice = device
            self.isScanning = false
        }
        delegate?.didConnectToDevice(device)
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        let device = BluetoothDevice(
            id: peripheral.identifier.uuidString,
            name: peripheral.name ?? "Disconnected Device",
            rssi: 0,
            peripheral: peripheral,
            isConnected: false
        )

        DispatchQueue.main.async {
            self.connectedDevice = nil
            self.connectedPeripheral = nil
            self.characteristic = nil
        }
        delegate?.didDisconnectFromDevice(device)

        if let error = error {
            delegate?.didEncounterError(error)
        }
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        if let error = error {
            delegate?.didEncounterError(error)
        }
    }
}

extension BluetoothManager: CBPeripheralDelegate {
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        if let error = error {
            delegate?.didEncounterError(error)
            return
        }

        for service in peripheral.services ?? [] {
            peripheral.discoverCharacteristics(nil, for: service)
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        if let error = error {
            delegate?.didEncounterError(error)
            return
        }

        for characteristic in service.characteristics ?? [] {
            if characteristic.properties.contains(.notify) {
                peripheral.setNotifyValue(true, for: characteristic)
            }
            if characteristic.properties.contains(.write) || characteristic.properties.contains(.writeWithoutResponse) {
                self.characteristic = characteristic
            }
            if characteristic.properties.contains(.read) {
                peripheral.readValue(for: characteristic)
            }
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            delegate?.didEncounterError(error)
            return
        }

        guard let data = characteristic.value else { return }

        DispatchQueue.main.async {
            self.receivedData = data
        }

        if let device = connectedDevice {
            delegate?.didReceiveData(data, from: device)
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            delegate?.didEncounterError(error)
        }
    }
}
