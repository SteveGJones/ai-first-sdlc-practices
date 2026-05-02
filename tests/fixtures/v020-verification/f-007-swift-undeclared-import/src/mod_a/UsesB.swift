// Module A — imports ModB without declared visibility (F-007 Swift defect)
import ModB

struct ModAService {
    func run() -> String { return ModBService().run() }
}
